# -*- coding: utf-8 -*-
"""
Module: gwo_llm_router_reward_shaper.py
Project: TALOS v5.10.2
Description:
    Bi-Level Multi-Objective Reward Shaping for the TALOS LLM Router using the
    canonical Grey Wolf Optimizer (GWO) described by Mirjalili et al. (2014).

    The module optimizes a four-dimensional reward weight vector
    ``w = [w_quality, w_latency, w_cost, w_penalty]`` subject to the simplex
    constraint ``sum(w) == 1.0`` and ``w_i >= 0.0``. The outer loop is a GWO
    wolf pack (alpha, beta, delta leaders) searching the continuous 4D
    hypercube; every candidate position is projected onto the simplex before
    evaluation. The inner loop evaluates the LLM Router under the reward
    shaping function::

        R = w_quality * QualityScore
            - w_latency * LatencyRatio
            - w_cost * CostRatio
            - w_penalty * RateLimitPenalty

    The inner evaluation is a self-contained, seedable surrogate of router
    telemetry so the optimizer remains fully air-gapped and deterministic. The
    ``_evaluate_router`` method is the single extension point where live router
    metrics (quality, latency, cost, rate-limit signals) may be substituted.

    The optimized weights and convergence trajectory are exported to
    ``models/gwo_llm_router_reward_weights.json`` together with three Pareto
    profile configurations (Deep Research, Fast Screening, Air-Gapped Local).

    Key design decisions:
    - Simplex projection guarantees the multi-objective weights always sum to 1.
    - GWO minimizes a scalar fitness; the shaper maximizes shaped reward, so
      fitness is defined as the negated reward.
    - Fresh r1/r2 (hence fresh A and C) are drawn independently for each of the
      alpha, beta, and delta encircling terms, per the canonical formulation.

Dependencies:
    - numpy: Vectorized wolf pack arithmetic and random sampling.
    - json, os, sys, time, argparse, datetime: Export, paths, CLI, and timing.
"""

import os
import sys

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

import argparse
import json
import time
from datetime import datetime

import numpy as np

from src.ai.drl.llm_router_subagent import LLMRouterSubAgent


# -- Canonical weight labels and defaults --------------------------------------
WEIGHT_LABELS = ["w_quality", "w_latency", "w_cost", "w_penalty"]
DIMENSIONS = len(WEIGHT_LABELS)

# -- Synthetic task types sampled by the inner-loop router evaluation --
_TASK_TYPES = ["deep_research", "fast_screening", "air_gapped_local"]

DEFAULT_WOLVES = 10
DEFAULT_ITERATIONS = 30
DEFAULT_EVAL_EPISODES = 20
DEFAULT_STD_THRESHOLD = 1e-4


# -- Pareto profile configurations (reference operating points) ----------------
PARETO_PROFILES = {
    "Deep Research": {
        "w_quality": 0.60, "w_latency": 0.10, "w_cost": 0.10, "w_penalty": 0.20,
    },
    "Fast Screening": {
        "w_quality": 0.25, "w_latency": 0.55, "w_cost": 0.10, "w_penalty": 0.10,
    },
    "Air-Gapped Local": {
        "w_quality": 0.45, "w_latency": 0.10, "w_cost": 0.40, "w_penalty": 0.05,
    },
}


class GWOLLMRouterRewardShaper:
    """Bi-Level GWO optimizer for the LLM Router reward weights.

    The outer GWO loop searches the 4D weight hypercube while the inner loop
    evaluates the LLM Router under the reward shaping function. Instances are
    configured with pack size, iteration budget, inner evaluation episodes, and
    an optional RNG seed for reproducibility.

    Attributes:
        wolves (int): Wolf pack population size.
        iterations (int): Maximum outer GWO iterations.
        eval_episodes (int): Inner evaluation episodes per fitness evaluation.
        seed (int | None): Random seed for deterministic runs.
        _rng (numpy.random.Generator): Seeded random number generator.
        trajectory (list of dict): Convergence trajectory of the alpha leader.
    """

    def __init__(self, wolves=DEFAULT_WOLVES, iterations=DEFAULT_ITERATIONS,
                 eval_episodes=DEFAULT_EVAL_EPISODES, seed=None):
        """Initialize the reward shaper.

        Args:
            wolves (int): Wolf pack size. Defaults to 10.
            iterations (int): Outer GWO iteration budget. Defaults to 30.
            eval_episodes (int): Inner router evaluation episodes. Defaults to 20.
            seed (int | None): Optional RNG seed. Defaults to None.
        """
        self.wolves = int(wolves)
        self.iterations = int(iterations)
        self.eval_episodes = int(eval_episodes)
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        self.trajectory = []

    # ------------------------------------------------------------------
    # -- Simplex projection --
    # ------------------------------------------------------------------
    @staticmethod
    def _project_simplex(vector):
        """Project a vector onto the probability simplex.

        Args:
            vector (numpy.ndarray): Unconstrained weight vector.

        Returns:
            numpy.ndarray: Projected vector with non-negative entries summing to 1.
        """
        clipped = np.clip(vector, 0.0, None)
        total = float(np.sum(clipped))
        if total <= 0.0:
            return np.full_like(clipped, 1.0 / len(clipped))
        return clipped / total

    # ------------------------------------------------------------------
    # -- Inner loop: LLM Router evaluation under reward shaping --
    # ------------------------------------------------------------------
    def _evaluate_router(self, weights):
        """Evaluate the LLMRouterSubAgent under the reward shaping function.

        Instantiates an ``LLMRouterSubAgent`` with the candidate weight vector,
        then routes ``eval_episodes`` synthetic requests (seeded prompt length
        and task type) through it. Each request yields the provider the
        sub-agent selects plus that provider's quality, latency, cost, and
        rate-limit signals; the shaped reward ``R`` is aggregated and averaged.

        Args:
            weights (numpy.ndarray): Normalized reward weights (length 4).

        Returns:
            float: Mean shaped reward across the evaluation episodes.
        """
        w_q, w_l, w_c, w_p = weights
        subagent = LLMRouterSubAgent()
        subagent.set_weights(weights)
        total_reward = 0.0

        for _ in range(self.eval_episodes):
            # -- Synthetic request workload (seeded) --
            prompt_length = int(self._rng.integers(64, 4097))
            task_type = self._rng.choice(_TASK_TYPES)
            provider = subagent.select_provider(prompt_length, task_type)
            quality, latency, cost, penalty = subagent.estimate_signals(
                prompt_length, task_type)[provider]

            # -- Per-request noise around the deterministic quality signal --
            noise = float(self._rng.normal(0.0, 0.01))
            reward = (w_q * (quality + noise)
                      - w_l * latency
                      - w_c * cost
                      - w_p * penalty)
            total_reward += reward

        return total_reward / self.eval_episodes

    # ------------------------------------------------------------------
    # -- Outer loop: canonical GWO position update --
    # ------------------------------------------------------------------
    def _fitness(self, weights):
        """Return the scalar fitness to minimize (negated shaped reward).

        Args:
            weights (numpy.ndarray): Normalized reward weights (length 4).

        Returns:
            float: Negative shaped reward.
        """
        return -self._evaluate_router(weights)

    def _update_position(self, wolf, dim, alpha, beta, delta, a_factor):
        """Update one dimension of a wolf position (Mirjalili 2014, Eq. 3.5-3.7).

        Fresh r1/r2 (hence fresh A and C) are drawn independently for each of
        the alpha, beta, and delta encircling terms.

        Args:
            wolf (numpy.ndarray): Candidate wolf position (length 4).
            dim (int): Dimension index being updated.
            alpha (numpy.ndarray): Alpha leader position.
            beta (numpy.ndarray): Beta leader position.
            delta (numpy.ndarray): Delta leader position.
            a_factor (float): Linearly decreasing exploration coefficient in [0, 2].

        Returns:
            float: Updated coordinate for the given dimension.
        """
        # -- Alpha term --
        r1, r2 = self._rng.random(2)
        a1 = 2.0 * a_factor * r1 - a_factor
        c1 = 2.0 * r2
        d_alpha = abs(c1 * alpha[dim] - wolf[dim])
        x1 = alpha[dim] - a1 * d_alpha

        # -- Beta term --
        r1, r2 = self._rng.random(2)
        a2 = 2.0 * a_factor * r1 - a_factor
        c2 = 2.0 * r2
        d_beta = abs(c2 * beta[dim] - wolf[dim])
        x2 = beta[dim] - a2 * d_beta

        # -- Delta term --
        r1, r2 = self._rng.random(2)
        a3 = 2.0 * a_factor * r1 - a_factor
        c3 = 2.0 * r2
        d_delta = abs(c3 * delta[dim] - wolf[dim])
        x3 = delta[dim] - a3 * d_delta

        return (x1 + x2 + x3) / 3.0

    # ------------------------------------------------------------------
    # -- Optimization orchestration --
    # ------------------------------------------------------------------
    def optimize(self):
        """Run the bi-level GWO optimization.

        Returns:
            dict: Best weights, best reward, convergence trajectory, and
                Pareto profile evaluations.
        """
        start_time = time.perf_counter()

        # -- Initialize and project the wolf pack onto the simplex --
        pack = self._rng.uniform(0.0, 1.0, size=(self.wolves, DIMENSIONS))
        pack = np.array([self._project_simplex(w) for w in pack])

        fitness = np.array([self._fitness(w) for w in pack])
        sorted_indices = np.argsort(fitness)
        alpha = pack[sorted_indices[0]].copy()
        beta = pack[sorted_indices[1]].copy()
        delta = pack[sorted_indices[2]].copy()

        self.trajectory = [{
            "iteration": 0,
            "alpha_reward": float(-fitness[sorted_indices[0]]),
            "a_factor": 2.0,
        }]

        # -- Outer GWO loop --
        for iteration in range(1, self.iterations + 1):
            a_factor = 2.0 - iteration * (2.0 / self.iterations)

            new_pack = []
            for wolf in pack:
                updated = np.array([
                    self._update_position(wolf, d, alpha, beta, delta, a_factor)
                    for d in range(DIMENSIONS)
                ])
                new_pack.append(self._project_simplex(np.clip(updated, 0.0, 1.0)))
            pack = np.array(new_pack)

            fitness = np.array([self._fitness(w) for w in pack])
            sorted_indices = np.argsort(fitness)
            alpha = pack[sorted_indices[0]].copy()
            beta = pack[sorted_indices[1]].copy()
            delta = pack[sorted_indices[2]].copy()

            self.trajectory.append({
                "iteration": iteration,
                "alpha_reward": float(-fitness[sorted_indices[0]]),
                "a_factor": a_factor,
            })

            # -- Early stop when the pack has effectively converged --
            if float(np.std(fitness)) < DEFAULT_STD_THRESHOLD:
                break

        best_weights = self._project_simplex(alpha)
        best_reward = float(-self._fitness(best_weights))
        elapsed = time.perf_counter() - start_time

        return {
            "best_weights": best_weights,
            "best_reward": best_reward,
            "elapsed_seconds": round(elapsed, 2),
        }

    # ------------------------------------------------------------------
    # -- Export --
    # ------------------------------------------------------------------
    @staticmethod
    def _models_dir():
        """Return the absolute ``models/`` directory path.

        Returns:
            str: Absolute path to the models directory.
        """
        project_root = _P if _P else os.getcwd()
        models_dir = os.path.join(project_root, "models")
        os.makedirs(models_dir, exist_ok=True)
        return models_dir

    def export(self, result):
        """Export optimized weights, trajectory, and Pareto profiles to JSON.

        Args:
            result (dict): Result dict returned by ``optimize``.

        Returns:
            str: Absolute path to the exported JSON file.
        """
        best = result["best_weights"]
        weight_map = {
            WEIGHT_LABELS[i]: round(float(best[i]), 6) for i in range(DIMENSIONS)
        }

        profile_evaluations = {}
        for name, profile in PARETO_PROFILES.items():
            vector = np.array([profile[label] for label in WEIGHT_LABELS])
            profile_evaluations[name] = {
                "weights": profile,
                "shaped_reward": round(self._evaluate_router(vector), 6),
            }

        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "version": "5.10.2",
            "optimizer": "GWOLLMRouterRewardShaper",
            "parameters": {
                "wolves": self.wolves,
                "iterations": self.iterations,
                "eval_episodes": self.eval_episodes,
                "seed": self.seed,
            },
            "best_weights": weight_map,
            "sum_check": round(sum(weight_map.values()), 6),
            "best_shaped_reward": round(result["best_reward"], 6),
            "elapsed_seconds": result["elapsed_seconds"],
            "convergence_trajectory": self.trajectory,
            "pareto_profiles": profile_evaluations,
        }

        output_path = os.path.join(self._models_dir(),
                                   "gwo_llm_router_reward_weights.json")
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

        return output_path

    # ------------------------------------------------------------------
    # -- CLI orchestration --
    # ------------------------------------------------------------------
    def run(self):
        """Run the optimizer and print a formatted summary.

        Returns:
            dict: The optimization result dict.
        """
        print("=" * 70)
        print("  TALOS GWO LLM Router Reward Shaper (Bi-Level, v5.10.2)")
        print("=" * 70)
        print(f"  Wolves (population):        {self.wolves}")
        print(f"  Max iterations:            {self.iterations}")
        print(f"  Inner evaluation episodes: {self.eval_episodes}")
        print(f"  Random seed:               {self.seed}")
        print(f"  Search space: w in [0, 1]^4, projected to sum(w) == 1.0")
        print()

        result = self.optimize()

        best = result["best_weights"]
        print("  Optimization complete.")
        print("  Best reward weights found by the Alpha wolf:")
        for i, label in enumerate(WEIGHT_LABELS):
            print(f"    {label:<12}: {best[i]:.6f}")
        print(f"  Sum check: {float(np.sum(best)):.6f}")
        print(f"  Best shaped reward: {result['best_reward']:.6f}")
        print(f"  Iterations performed: {len(self.trajectory) - 1}")
        print(f"  Time: {result['elapsed_seconds']} seconds")

        output_path = self.export(result)
        print(f"\n  Weights, trajectory, and Pareto profiles saved to:")
        print(f"    {output_path}")
        print("=" * 70)

        return result


def main():
    """Parse CLI arguments and launch the reward shaper."""
    parser = argparse.ArgumentParser(
        description="GWO LLM Router Reward Shaper (Bi-Level Multi-Objective)"
    )
    parser.add_argument("--wolves", type=int, default=DEFAULT_WOLVES,
                        help="Wolf pack population size (default: 10).")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS,
                        help="Maximum outer GWO iterations (default: 30).")
    parser.add_argument("--eval-episodes", type=int, default=DEFAULT_EVAL_EPISODES,
                        help="Inner router evaluation episodes (default: 20).")
    parser.add_argument("--seed", type=int, default=None,
                        help="Optional RNG seed for reproducible runs.")
    args = parser.parse_args()

    shaper = GWOLLMRouterRewardShaper(
        wolves=args.wolves,
        iterations=args.iterations,
        eval_episodes=args.eval_episodes,
        seed=args.seed,
    )
    shaper.run()


if __name__ == "__main__":
    main()
