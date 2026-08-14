# -*- coding: utf-8 -*-
"""
Module: gwo_rl_optimizer.py (v2.0 — Real Fitness + Canonical GWO)
Project: TALOS v5.9.18
Description:
    Grey Wolf Optimizer (GWO) for TALOS DRL hyperparameter tuning.
    v1.1 adds: --live flag for real-time GUI progress, _write_live_progress(),
    gwo_progress.json output for Streamlit dashboard.
    v2.0 (BATCH 1 audit fixes):
    - calculate_fitness() now ACTUALLY trains the agent: transitions are
      stored in replay memory, agent.learn() is called each step, and the
      decayed epsilon is passed to act(). Fitness is measured in a separate
      GREEDY evaluation phase (eps=0.0), so lr/gamma/eps_decay are causally
      connected to the fitness value. (Previously fitness was pure random-walk
      noise: eps=1.0 was hardcoded and learn() was never called.)
    - update_wolf_position() now follows canonical GWO (Mirjalili 2014):
      fresh r1/r2 (hence fresh A and C) are drawn INDEPENDENTLY for each of
      the alpha, beta and delta encircling terms (Eq. 3.5–3.7).
    - Fitness values are computed ONCE per iteration and cached — they are
      passed into _build_history_entry() instead of being re-evaluated
      (mandatory now that each fitness eval trains a full agent).

    Usage:
        python scripts/gwo_rl_optimizer.py              # default: 15 wolves, 50 iters
        python scripts/gwo_rl_optimizer.py --wolves 20 --iters 100
        python scripts/gwo_rl_optimizer.py --live       # writes gwo_progress.json
"""
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import argparse
import numpy as np
from time import perf_counter

from src.ai.drl.talos_env import TalosEnv
from src.ai.drl.drl_agent import TalosDRLAgent, Transition

DEFAULT_WOLVES = 15
DEFAULT_ITERS = 50
DEFAULT_STD_THRESH = 0.01
DEFAULT_RL_EPISODES = 30
DEFAULT_RL_STEPS = 200
# Number of greedy (eps=0.0) evaluation episodes run AFTER training to
# measure fitness. Kept small — evaluation is deterministic-policy rollout.
EVAL_EPISODES = 5

LOWER_BOUND = np.array([-5.0, 0.5, 0.9])
UPPER_BOUND = np.array([-3.0, 0.99, 0.999])


def _build_history_entry(iteration, wolves, best_wolves, wolves_number, fitness_values):
    """Build one history record. Uses CACHED fitness_values (v2.0) —
    re-evaluating fitness here would retrain an agent per wolf (2x runtime)
    and, because fitness is stochastic, would log values inconsistent with
    the ranking used to pick alpha/beta/delta."""
    alpha_pos = best_wolves[0][0]
    beta_pos = best_wolves[1][0]
    delta_pos = best_wolves[2][0]
    wolves_list = []
    for w in range(wolves_number):
        lr, gamma, eps_d = decode_wolf(wolves[w])
        fitness = -float(fitness_values[w])
        if np.array_equal(wolves[w], alpha_pos): role = "alpha"
        elif np.array_equal(wolves[w], beta_pos): role = "beta"
        elif np.array_equal(wolves[w], delta_pos): role = "delta"
        else: role = "omega"
        wolves_list.append({"lr": round(lr, 10), "gamma": round(gamma, 6),
                           "eps_d": round(eps_d, 6), "fitness": round(fitness, 2), "role": role})
    return {"iteration": iteration, "alpha_fitness": -best_wolves[0][1],
            "beta_fitness": -best_wolves[1][1], "delta_fitness": -best_wolves[2][1],
            "wolves": wolves_list}


def decode_wolf(wolf_position):
    learning_rate = 10.0 ** wolf_position[0]
    gamma = float(wolf_position[1])
    eps_decay = float(wolf_position[2])
    return learning_rate, gamma, eps_decay


def calculate_fitness(wolf_position):
    """Train a fresh DDQN agent with the candidate hyperparameters, then
    measure average greedy-policy reward. Returns NEGATIVE reward (GWO
    minimizes). v2.0: the agent is actually trained (store + learn + decayed
    epsilon), so the hyperparameters causally affect fitness."""
    lr, gamma, eps_decay = decode_wolf(wolf_position)
    env = TalosEnv()
    from src.ai.drl import drl_agent as da
    old_lr, old_gamma = da.LR, da.GAMMA
    # Monkey-patch module globals — learn() reads GAMMA at call time.
    da.LR, da.GAMMA = lr, gamma
    try:
        agent = TalosDRLAgent()
        # Rebuild optimizer with the candidate learning rate.
        agent.actor_optimizer = agent.actor_optimizer.__class__(
            agent.actor_online.parameters(), lr=lr)

        # ── Phase 1: TRAINING (epsilon-greedy with candidate eps_decay) ──
        epsilon = 1.0
        for _ in range(DEFAULT_RL_EPISODES):
            obs, _ = env.reset()
            agent.reset_hidden_states()
            for _ in range(DEFAULT_RL_STEPS):
                action = agent.act(obs, eps=epsilon)
                next_obs, reward, terminated, truncated, _ = env.step(action)
                # Store DONE=terminated only (truncation must still bootstrap).
                agent.memory.store(Transition(obs, action, reward, next_obs, terminated))
                agent.learn()
                obs = next_obs
                if terminated or truncated:
                    break
            epsilon = max(0.01, epsilon * eps_decay)

        # ── Phase 2: GREEDY EVALUATION (eps=0.0, no learning) ──
        total_reward = 0.0
        for _ in range(EVAL_EPISODES):
            obs, _ = env.reset()
            agent.reset_hidden_states()
            for _ in range(DEFAULT_RL_STEPS):
                action = agent.act(obs, eps=0.0)
                next_obs, reward, terminated, truncated, _ = env.step(action)
                total_reward += reward
                obs = next_obs
                if terminated or truncated:
                    break
        return -(total_reward / EVAL_EPISODES)
    finally:
        da.LR, da.GAMMA = old_lr, old_gamma


def find_best_three_wolves(wolves_positions):
    """Evaluate all wolves ONCE and return (best_three, std, all_fitness).
    v2.0: also returns the cached fitness array for history logging."""
    fitness_values = np.array([calculate_fitness(w) for w in wolves_positions])
    sorted_indices = np.argsort(fitness_values)
    best_wolves = {
        0: [wolves_positions[sorted_indices[0]].copy(), fitness_values[sorted_indices[0]]],
        1: [wolves_positions[sorted_indices[1]].copy(), fitness_values[sorted_indices[1]]],
        2: [wolves_positions[sorted_indices[2]].copy(), fitness_values[sorted_indices[2]]],
    }
    return best_wolves, np.std(fitness_values), fitness_values


def update_wolf_position(wolf_pos, dim, best_wolves, a_factor):
    """Canonical GWO position update (Mirjalili 2014, Eq. 3.5–3.7).
    v2.0: fresh r1/r2 (hence fresh A and C) are drawn INDEPENDENTLY for
    each of the alpha, beta and delta encircling terms."""
    # ── Alpha term ──
    r1, r2 = np.random.random(2)
    A1, C1 = 2.0 * a_factor * r1 - a_factor, 2.0 * r2
    D_alpha = abs(C1 * best_wolves[0][0][dim] - wolf_pos)
    X1 = best_wolves[0][0][dim] - A1 * D_alpha
    # ── Beta term ──
    r1, r2 = np.random.random(2)
    A2, C2 = 2.0 * a_factor * r1 - a_factor, 2.0 * r2
    D_beta = abs(C2 * best_wolves[1][0][dim] - wolf_pos)
    X2 = best_wolves[1][0][dim] - A2 * D_beta
    # ── Delta term ──
    r1, r2 = np.random.random(2)
    A3, C3 = 2.0 * a_factor * r1 - a_factor, 2.0 * r2
    D_delta = abs(C3 * best_wolves[2][0][dim] - wolf_pos)
    X3 = best_wolves[2][0][dim] - A3 * D_delta
    return (X1 + X2 + X3) / 3.0


def _write_live_progress(iteration, max_iters, best_reward, best_fitness, a_factor, status="running"):
    import os as _os, json as _json
    project_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
    models_dir = _os.path.join(project_root, "models")
    _os.makedirs(models_dir, exist_ok=True)
    progress_path = _os.path.join(models_dir, "gwo_progress.json")
    data = {"iteration": iteration, "max_iterations": max_iters,
            "best_reward": round(best_reward, 1), "best_fitness": round(best_fitness, 1),
            "a_factor": round(a_factor, 3), "status": status}
    with open(progress_path, "w", encoding="utf-8") as f:
        _json.dump(data, f)


def run_gwo(wolves_number=DEFAULT_WOLVES, max_iterations=DEFAULT_ITERS, live=False):
    start_time = perf_counter()
    print("=" * 65)
    print("  TALOS GWO Hyperparameter Optimizer")
    print("=" * 65)
    print(f"  Wolves (population): {wolves_number}")
    print(f"  Max iterations: {max_iterations}")
    print(f"  Search space: lr in [1e-5, 1e-3], gamma in [0.5, 0.99], eps_decay in [0.9, 0.999]")
    print(f"  RL episodes per fitness eval: {DEFAULT_RL_EPISODES}")
    print()

    wolves = np.random.uniform(low=LOWER_BOUND, high=UPPER_BOUND, size=(wolves_number, 3))
    print("  [ITER 0] Initialising population and finding leaders...")
    best_wolves, fitness_std, fitness_values = find_best_three_wolves(wolves)

    a_factor, iteration = 2.0, 0
    import os as _os, json as _json
    project_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
    models_dir = _os.path.join(project_root, "models")
    _os.makedirs(models_dir, exist_ok=True)

    gwo_history = [_build_history_entry(iteration, wolves, best_wolves, wolves_number, fitness_values)]

    # Write initial history for Dash live dashboard
    history_path = _os.path.join(models_dir, "gwo_history.json")
    with open(history_path, "w", encoding="utf-8") as f:
        _json.dump(gwo_history, f)

    # Write initial progress for GUI
    if live:
        _write_live_progress(0, max_iterations, -best_wolves[0][1], best_wolves[0][1], a_factor)

    while iteration < max_iterations and fitness_std > DEFAULT_STD_THRESH:
        iteration += 1
        for w in range(wolves_number):
            for d in range(3):
                wolves[w, d] = np.clip(update_wolf_position(wolves[w, d], d, best_wolves, a_factor),
                                       LOWER_BOUND[d], UPPER_BOUND[d])
        a_factor = 2.0 - iteration * (2.0 / max_iterations)
        best_wolves, fitness_std, fitness_values = find_best_three_wolves(wolves)
        gwo_history.append(_build_history_entry(iteration, wolves, best_wolves, wolves_number, fitness_values))

        # Write history incrementally so Dash live dashboard can read it
        with open(history_path, "w", encoding="utf-8") as f:
            _json.dump(gwo_history, f)

        best_lr, best_gamma, best_eps = decode_wolf(best_wolves[0][0])
        best_reward = -best_wolves[0][1]
        print(f"  [ITER {iteration:2d}] a={a_factor:.3f}  "
              f"α: lr={best_lr:.2e} γ={best_gamma:.3f} εd={best_eps:.4f}  "
              f"fitness={best_wolves[0][1]:.1f} (avg_reward={best_reward:.1f})  "
              f"std={fitness_std:.4f}")
        if live:
            _write_live_progress(iteration, max_iterations, best_reward, best_wolves[0][1], a_factor)

    end_time = perf_counter()
    elapsed = end_time - start_time
    best_lr, best_gamma, best_eps = decode_wolf(best_wolves[0][0])
    best_reward = -best_wolves[0][1]

    print("\n" + "=" * 65)
    print("  OPTIMISATION COMPLETE")
    print("=" * 65)
    print(f"  Best hyperparameters found by Alpha wolf:")
    print(f"    Learning rate:   {best_lr:.6e}")
    print(f"    Gamma:           {best_gamma:.4f}")
    print(f"    Epsilon decay:   {best_eps:.6f}")
    print(f"  Best average reward: {best_reward:.1f} over {DEFAULT_RL_EPISODES} episodes")
    print(f"  Time: {elapsed:.1f} seconds")
    print(f"  Iterations: {iteration}")
    print("=" * 65)

    json_path = _os.path.join(models_dir, "gwo_best_params.json")
    params = {"learning_rate": best_lr, "gamma": best_gamma, "epsilon_decay": best_eps,
              "best_fitness": best_wolves[0][1], "best_avg_reward": best_reward,
              "iterations": iteration, "gwo_time_seconds": round(elapsed, 1)}
    with open(json_path, "w", encoding="utf-8") as f: _json.dump(params, f, indent=2)
    print(f"\n  Best parameters saved to: models/gwo_best_params.json")

    print(f"  GWO history saved to: models/gwo_history.json")
    print(f"     {len(gwo_history)} iterations, {wolves_number} wolves each (already written live)")

    if live:
        _write_live_progress(iteration, max_iterations, best_reward, best_wolves[0][1], a_factor, status="complete")

    return {"learning_rate": best_lr, "gamma": best_gamma, "epsilon_decay": best_eps,
            "best_reward": best_reward, "iterations": iteration, "gwo_time": elapsed}


def main():
    parser = argparse.ArgumentParser(description='GWO Hyperparameter Optimizer for TALOS DRL Agent')
    parser.add_argument('--wolves', type=int, default=DEFAULT_WOLVES)
    parser.add_argument('--iters', type=int, default=DEFAULT_ITERS)
    parser.add_argument('--rl-episodes', type=int, default=DEFAULT_RL_EPISODES)
    parser.add_argument('--live', action='store_true',
                        help='Write per-iteration progress to models/gwo_progress.json for GUI')
    args = parser.parse_args()
    import src.ai.optimizers.gwo_rl_optimizer as _self
    _self.DEFAULT_RL_EPISODES = args.rl_episodes
    run_gwo(args.wolves, args.iters, live=args.live)


if __name__ == "__main__":
    main()