# -*- coding: utf-8 -*-
"""
Module: llm_router_subagent.py
Project: TALOS v5.10.2
Description:
    LLM Router Sub-Agent that selects the optimal active provider for a given
    inference request. It loads the multi-objective reward weights produced by
    the GWO reward shaper (``models/gwo_llm_router_reward_weights.json``) and
    falls back to a default Pareto profile when the artifact is absent. For
    every candidate request it evaluates the prompt token length, the current
    provider rate-limit status, and latency against a static provider profile
    table, then scores each provider with the shaped reward function::

        R = w_quality * QualityScore
            - w_latency * LatencyRatio
            - w_cost * CostRatio
            - w_penalty * RateLimitPenalty

    The provider maximizing ``R`` is returned. The sub-agent is deliberately
    self-contained (it imports no TALOS core modules) so it can be consumed by
    both ``AIManager`` (for live routing) and the GWO reward shaper (for the
    inner-loop evaluation) without circular imports. All methods are
    deterministic: stochasticity is injected by callers.

    Key design decisions:
    - A static ``PROVIDER_PROFILES`` table encodes base quality, latency, cost,
      and rate-limit signals for the seven canonical providers (local, nvidia,
      groq, cerebras, github, gemini, deepseek).
    - Prompt length and task type modulate the signals so longer prompts and
      deep-research tasks shift cost/latency/quality trade-offs realistically.
    - ``select_provider`` is constrained to an explicit active-provider list so
      the caller (AIManager) can restrict routing to configured, circuit-closed
      providers only.

Dependencies:
    - json: Loading the optimized reward weights artifact.
    - os, sys: Project-root resolution and model path construction.
    - numpy: Signal clipping and normalization arithmetic.
"""
import json
import os
import sys

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

import numpy as np


# -- Canonical weight labels -----------------------------------------------
WEIGHT_LABELS = ["w_quality", "w_latency", "w_cost", "w_penalty"]

# -- Default Pareto profile weights (fallback when no optimized JSON exists) --
DEFAULT_WEIGHTS = {
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
# Default profile used when no task-specific override is requested.
DEFAULT_PROFILE = "Fast Screening"

# -- Static provider profiles (base signals, all in [0, 1]) -------------------
# quality: higher is better. latency/cost/penalty: higher is worse.
# penalty is the rate-limit penalty incurred by that provider.
PROVIDER_PROFILES = {
    "local":    {"quality": 0.55, "latency": 0.35, "cost": 0.05, "penalty": 0.05},
    "nvidia":   {"quality": 0.78, "latency": 0.30, "cost": 0.45, "penalty": 0.25},
    "groq":     {"quality": 0.72, "latency": 0.10, "cost": 0.30, "penalty": 0.30},
    "cerebras": {"quality": 0.74, "latency": 0.12, "cost": 0.35, "penalty": 0.28},
    "github":   {"quality": 0.68, "latency": 0.40, "cost": 0.20, "penalty": 0.35},
    "gemini":   {"quality": 0.85, "latency": 0.45, "cost": 0.40, "penalty": 0.40},
    "deepseek": {"quality": 0.80, "latency": 0.50, "cost": 0.25, "penalty": 0.35},
}

# -- Task-type modifiers: prompt-length scale and quality bias ---------------
# deep_research favors longer, higher-quality prompts; fast_screening favors
# short, low-latency prompts; air_gapped_local maps to local-friendly routing.
TASK_MODIFIERS = {
    "deep_research":    {"prompt_scale": 1.4, "quality_bias": 0.05},
    "fast_screening":   {"prompt_scale": 0.6, "quality_bias": -0.02},
    "air_gapped_local": {"prompt_scale": 0.8, "quality_bias": 0.00},
    "default":          {"prompt_scale": 1.0, "quality_bias": 0.00},
}


class LLMRouterSubAgent:
    """Selects the optimal active provider for an LLM inference request.

    Attributes:
        weights (dict): Normalized reward weights (the four ``WEIGHT_LABELS``
            keys summing to 1.0). Loaded from the shaper JSON or a default
            Pareto profile on construction.
    """

    def __init__(self, weights_path=None):
        """Initialize the sub-agent with reward weights.

        Args:
            weights_path (str | None): Path to the weights JSON. When None, the
                canonical ``models/gwo_llm_router_reward_weights.json`` is used
                with graceful fallback to the default Pareto profile.
        """
        self.weights = self._normalize(self.load_weights(weights_path))

    @staticmethod
    def _normalize(weights_dict):
        """Normalize a weight mapping to the simplex over the four labels.

        Args:
            weights_dict (dict): Mapping of weight labels to numeric values.

        Returns:
            dict: Normalized weights summing to 1.0, all non-negative.
        """
        values = np.array(
            [float(weights_dict.get(label, 0.0)) for label in WEIGHT_LABELS]
        )
        values = np.clip(values, 0.0, None)
        total = float(values.sum())
        if total <= 0.0:
            values = np.full(len(WEIGHT_LABELS), 0.25)
            total = 1.0
        return {label: float(values[i] / total) for i, label in enumerate(WEIGHT_LABELS)}

    @staticmethod
    def load_weights(path=None):
        """Load optimized reward weights from JSON with Pareto fallback.

        Args:
            path (str | None): Explicit JSON path. When None, the canonical
                ``models/gwo_llm_router_reward_weights.json`` is resolved.

        Returns:
            dict: A mapping of the four weight labels to floats.
        """
        if path is None:
            project_root = _P if _P else os.getcwd()
            path = os.path.join(project_root, "models",
                                "gwo_llm_router_reward_weights.json")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            best = data.get("best_weights")
            if isinstance(best, dict) and all(label in best for label in WEIGHT_LABELS):
                return {label: float(best[label]) for label in WEIGHT_LABELS}
        except (OSError, ValueError, TypeError):
            pass
        return dict(DEFAULT_WEIGHTS[DEFAULT_PROFILE])

    def set_weights(self, weights):
        """Replace the active reward weights (e.g. a GWO candidate vector).

        Args:
            weights (dict | numpy.ndarray): Raw weights over the four labels.
        """
        if hasattr(weights, "tolist"):
            weights = dict(zip(WEIGHT_LABELS, [float(x) for x in weights]))
        self.weights = self._normalize(weights)

    def estimate_signals(self, prompt_length, task_type="default"):
        """Estimate per-provider (quality, latency, cost, penalty) signals.

        Args:
            prompt_length (int): Prompt length in tokens.
            task_type (str): One of ``TASK_MODIFIERS`` keys.

        Returns:
            dict: Provider name mapped to a 4-tuple
                ``(quality, latency, cost, penalty)``.
        """
        modifier = TASK_MODIFIERS.get(task_type, TASK_MODIFIERS["default"])
        load = float(np.clip(
            (prompt_length or 0) * modifier["prompt_scale"] / 4096.0, 0.0, 1.0
        ))

        signals = {}
        for name, profile in PROVIDER_PROFILES.items():
            quality = float(np.clip(profile["quality"] + modifier["quality_bias"], 0.0, 1.0))
            latency = float(np.clip(profile["latency"] * (0.6 + 0.8 * load), 0.0, 1.0))
            cost = float(np.clip(profile["cost"] * (0.5 + 0.5 * load), 0.0, 1.0))
            penalty = float(np.clip(profile["penalty"] * (0.7 + 0.6 * load), 0.0, 1.0))
            signals[name] = (quality, latency, cost, penalty)
        return signals

    def score_provider(self, signals):
        """Score a provider's signals under the shaped reward function.

        Args:
            signals (tuple): ``(quality, latency, cost, penalty)``.

        Returns:
            float: The shaped reward score.
        """
        quality, latency, cost, penalty = signals
        weights = self.weights
        return (weights["w_quality"] * quality
                - weights["w_latency"] * latency
                - weights["w_cost"] * cost
                - weights["w_penalty"] * penalty)

    def select_provider(self, prompt_length, task_type="default",
                        active_providers=None):
        """Select the optimal active provider for a request.

        Args:
            prompt_length (int): Prompt length in tokens.
            task_type (str): Routing task type (``TASK_MODIFIERS`` key).
            active_providers (list of str | None): Restrict candidates to these
                provider names. When None, all seven canonical providers are
                considered.

        Returns:
            str | None: The best provider name, or None if no provider matches.
        """
        if active_providers is None:
            active_providers = list(PROVIDER_PROFILES.keys())
        elif isinstance(active_providers, str):
            active_providers = [active_providers]

        active = [p for p in active_providers if p in PROVIDER_PROFILES]
        if not active:
            return None

        signals = self.estimate_signals(prompt_length, task_type)
        best_provider = None
        best_score = -np.inf
        for provider in active:
            score = self.score_provider(signals[provider])
            if score > best_score:
                best_score = score
                best_provider = provider
        return best_provider

