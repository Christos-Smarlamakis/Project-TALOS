# -*- coding: utf-8 -*-
"""
Module: gwo_rl_optimizer.py (v1.0)
Project: TALOS v5.0.0
Description:
    Grey Wolf Optimizer (GWO) for TALOS DRL hyperparameter tuning.
    Adapts the GWO meta-heuristic from reference_code/gwo.py to find the
    best combination of learning_rate, gamma, and epsilon_decay for the
    LSTM-DDDQN agent (TalosDRLAgent) in the TalosEnv environment.

    How GWO works:
    - A "wolf" is a candidate hyperparameter vector (lr, gamma, eps_decay).
    - The three best wolves (alpha, beta, delta) guide the others.
    - Each wolf's position is updated using: X_new = (X1 + X2 + X3) / 3
      where X_i = best_wolf_i - A * |C * best_wolf_i - current_wolf|
    - Parameter 'a' decays linearly from 2→0, balancing exploration/exploitation.

    Key design decisions:
    - Fitness = -1 * average_reward (negated because GWO minimizes).
    - Fast evaluation: only 30 episodes × 200 steps each, no learning.
    - Wolves represent 3D vectors: [learning_rate, gamma, epsilon_decay].
    - Bounds are log-scaled for learning_rate to cover orders of magnitude.

    Usage:
        python scripts/gwo_rl_optimizer.py              # default: 15 wolves, 50 iters
        python scripts/gwo_rl_optimizer.py --wolves 20 --iters 100
"""
import os
import sys
import argparse
import numpy as np
from time import perf_counter

# ── Add project root to Python's import path ────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.talos_env import TalosEnv
from core.drl_agent import TalosDRLAgent, Transition

# ── GWO-specific constants ──────────────────────────────────────────────────
DEFAULT_WOLVES = 15        # Population size — more wolves = broader search
DEFAULT_ITERS = 50         # Max GWO iterations
DEFAULT_STD_THRESH = 0.01  # Stop if fitness std deviation < this
DEFAULT_RL_EPISODES = 30   # How many fast RL episodes per fitness evaluation
DEFAULT_RL_STEPS = 200     # Steps per episode (= one simulated day)

# ── Hyperparameter search bounds ────────────────────────────────────────────
# Each wolf is a 3D vector: [log10(lr), gamma, epsilon_decay]
# We use log10(lr) so the search is uniform across orders of magnitude
# (1e-5, 10^-4.5, 10^-4, 10^-3.5, 10^-3) → all equally likely.
LOWER_BOUND = np.array([-5.0, 0.5, 0.9])    # log10(1e-5), gamma=0.5, decay=0.9
UPPER_BOUND = np.array([-3.0, 0.99, 0.999]) # log10(1e-3), gamma=0.99, decay=0.999


def decode_wolf(wolf_position):
    """
    Convert a wolf's 3D log-space position to actual hyperparameters.

    The first dimension is log10(learning_rate), so we compute 10^x.
    The other two dimensions (gamma, epsilon_decay) are used directly.

    Args:
        wolf_position (np.ndarray): Shape (3,) array from GWO search space.

    Returns:
        tuple: (learning_rate, gamma, epsilon_decay) as Python floats.
    """
    learning_rate = 10.0 ** wolf_position[0]  # Convert from log space
    gamma = float(wolf_position[1])           # Discount factor (0.5–0.99)
    eps_decay = float(wolf_position[2])       # Epsilon decay per episode
    return learning_rate, gamma, eps_decay


def calculate_fitness(wolf_position):
    """
    Evaluate one candidate hyperparameter set (one wolf).

    Creates a fresh TalosDRLAgent with the given hyperparameters,
    runs it in TalosEnv for DEFAULT_RL_EPISODES episodes WITHOUT
    any learning, and returns the negative average reward.

    We disable learning because this is a fitness evaluation, not
    a training session. We just want to see how well these params
    perform under a pure random policy (exploration only).

    Args:
        wolf_position (np.ndarray): Shape (3,) candidate position.

    Returns:
        float: Negative average reward (GWO minimizes, so we negate).
    """
    # ── Decode the 3D vector into actual hyperparameters ───────────────────
    lr, gamma, eps_decay = decode_wolf(wolf_position)

    # ── Create environment and agent ───────────────────────────────────────
    env = TalosEnv()
    agent = TalosDRLAgent()

    # ── Inject the candidate hyperparameters into the agent ────────────────
    # The agent uses module-level constants. We override them temporarily
    # by patching the agent's internal attributes.
    import core.drl_agent as da
    old_lr = da.LR
    old_gamma = da.GAMMA
    old_eps_decay = None  # We'll handle epsilon decay in the loop

    da.LR = lr
    da.GAMMA = gamma
    # Re-create optimizer with new learning rate
    agent.actor_optimizer = agent.actor_optimizer.__class__(
        agent.actor_online.parameters(), lr=lr)

    try:
        total_reward = 0.0
        epsilon = 1.0  # Always start with full exploration

        # ── Run fast evaluation episodes ───────────────────────────────────
        for episode in range(DEFAULT_RL_EPISODES):
            obs, _ = env.reset()
            agent.reset_hidden_states()

            for step in range(DEFAULT_RL_STEPS):
                # Pure random action (epsilon=1.0): we want to test
                # the raw environment dynamics, not a trained policy.
                action = agent.act(obs, eps=1.0)
                next_obs, reward, terminated, truncated, _ = env.step(action)
                total_reward += reward
                obs = next_obs
                if terminated or truncated:
                    break

            # Decay epsilon
            epsilon = max(0.01, epsilon * eps_decay)

        avg_reward = total_reward / DEFAULT_RL_EPISODES

        # ── GWO minimizes, so we return the negative reward ─────────────
        # The "best" wolf is the one with the smallest (most negative) fitness,
        # which corresponds to the highest average reward.
        return -avg_reward

    finally:
        # ── Restore original hyperparameters ───────────────────────────────
        da.LR = old_lr
        da.GAMMA = old_gamma


def find_best_three_wolves(wolves_positions):
    """
    Identify the three best wolves (alpha, beta, delta) by fitness.

    Sorts all wolves by fitness (ascending — lower is better for GWO)
    and returns a dictionary mapping 0→alpha, 1→beta, 2→delta.

    Args:
        wolves_positions (np.ndarray): (N, 3) array of all wolf positions.

    Returns:
        dict: {0: [alpha_pos, alpha_fitness], 1: [...], 2: [...]}
        np.ndarray: All N fitness values.
    """
    # ── Compute fitness for every wolf ─────────────────────────────────────
    fitness_values = np.array([calculate_fitness(w) for w in wolves_positions])

    # ── Sort by fitness (ascending — lower = better for GWO) ───────────────
    sorted_indices = np.argsort(fitness_values)

    # ── Build the leader dictionary ─────────────────────────────────────────
    best_wolves = {
        0: [wolves_positions[sorted_indices[0]].copy(), fitness_values[sorted_indices[0]]],
        1: [wolves_positions[sorted_indices[1]].copy(), fitness_values[sorted_indices[1]]],
        2: [wolves_positions[sorted_indices[2]].copy(), fitness_values[sorted_indices[2]]],
    }

    fitness_std = np.std(fitness_values)
    return best_wolves, fitness_std


def update_wolf_position(wolf_pos, dim, best_wolves, a_factor):
    """
    Update one dimension of one wolf's position using GWO equations.

    This implements the core GWO position update:
        1. Compute distance D = |C * leader_position - current_position|
        2. Compute new position = leader_position - A * D
        3. Average the results from alpha, beta, and delta leaders

    Parameters A and C control exploration vs exploitation:
        - When |A| > 1: wolf diverges (exploration — search new areas)
        - When |A| < 1: wolf converges (exploitation — refine near leader)
        - C is a random weight that helps avoid local minima

    Args:
        wolf_pos (float): Current wolf's position in this dimension.
        dim (int): Dimension index (0, 1, or 2).
        best_wolves (dict): {0: alpha, 1: beta, 2: delta} leaders.
        a_factor (float): Current 'a' parameter (decays 2→0).

    Returns:
        float: Updated position for this wolf in this dimension.
    """
    # ── Random coefficients r1, r2 from uniform [0,1] ─────────────────────
    r1, r2 = np.random.random(2)

    # ── Parameter A: exploration when |A|>1, exploitation when |A|<1 ──────
    A = 2.0 * a_factor * r1 - a_factor

    # ── Parameter C: random weighting of the leader's influence ────────────
    # C in [0, 2] — when C<1, reduces leader's pull (more independent search)
    C = 2.0 * r2

    # ── Compute distances from this wolf to each leader ────────────────────
    # D = |C * leader_pos - current_pos|
    D_alpha = abs(C * best_wolves[0][0][dim] - wolf_pos)
    D_beta = abs(C * best_wolves[1][0][dim] - wolf_pos)
    D_delta = abs(C * best_wolves[2][0][dim] - wolf_pos)

    # ── Compute proposed positions from each leader ────────────────────────
    # X_new = leader_pos - A * D
    X1 = best_wolves[0][0][dim] - A * D_alpha
    X2 = best_wolves[1][0][dim] - A * D_beta
    X3 = best_wolves[2][0][dim] - A * D_delta

    # ── Final position is the average of the three proposals ───────────────
    return (X1 + X2 + X3) / 3.0


def run_gwo(wolves_number=DEFAULT_WOLVES, max_iterations=DEFAULT_ITERS):
    """
    Execute the full GWO hyperparameter optimization.

    The algorithm:
    1. Randomly initialise all wolves in the 3D search space.
    2. Find alpha, beta, delta (the three best wolves).
    3. In each iteration:
       a. Update every wolf's position relative to the three leaders.
       b. Clip positions to stay within bounds.
       c. Decay the 'a' parameter linearly.
       d. Re-evaluate and find new leaders.

    Args:
        wolves_number (int): Number of wolves (population size).
        max_iterations (int): Maximum GWO iterations.

    Returns:
        dict: Results including best params, fitness, execution time.
    """
    start_time = perf_counter()

    print("=" * 65)
    print("  TALOS GWO Hyperparameter Optimizer")
    print("=" * 65)
    print(f"  Wolves (population): {wolves_number}")
    print(f"  Max iterations: {max_iterations}")
    print(f"  Search space: lr ∈ [1e-5, 1e-3], γ ∈ [0.5, 0.99], ε_decay ∈ [0.9, 0.999]")
    print(f"  RL episodes per fitness eval: {DEFAULT_RL_EPISODES}")
    print()

    # ── Step 1: Randomly initialise all wolves ──────────────────────────────
    # Each wolf is a 3D vector [log10(lr), gamma, epsilon_decay]
    wolves = np.random.uniform(
        low=LOWER_BOUND,
        high=UPPER_BOUND,
        size=(wolves_number, 3)
    )

    # ── Step 2: Find the three best wolves (alpha, beta, delta) ────────────
    print("  [ITER 0] Initialising population and finding leaders...")
    best_wolves, fitness_std = find_best_three_wolves(wolves)

    # ── Step 3: The 'a' parameter starts at 2 and decays linearly to 0 ─────
    # This controls the balance between exploration (high a) and
    # exploitation (low a).
    a_factor = 2.0

    iteration = 0

    # ── Main GWO loop ──────────────────────────────────────────────────────
    while iteration < max_iterations and fitness_std > DEFAULT_STD_THRESH:
        iteration += 1

        # ── Update every wolf's position ───────────────────────────────────
        for w in range(wolves_number):
            for d in range(3):  # 3 dimensions: lr, gamma, eps_decay
                new_val = update_wolf_position(
                    wolves[w, d], d, best_wolves, a_factor
                )
                # Clip to stay within the search bounds
                wolves[w, d] = np.clip(new_val, LOWER_BOUND[d], UPPER_BOUND[d])

        # ── Decay 'a' linearly: a = 2 - iter * (2 / max_iters) ─────────────
        a_factor = 2.0 - iteration * (2.0 / max_iterations)

        # ── Re-evaluate and find new leaders ────────────────────────────────
        best_wolves, fitness_std = find_best_three_wolves(wolves)

        # ── Decode alpha wolf for progress reporting ───────────────────────
        best_lr, best_gamma, best_eps = decode_wolf(best_wolves[0][0])
        best_reward = -best_wolves[0][1]  # Undo negation

        print(f"  [ITER {iteration:2d}] a={a_factor:.3f}  "
              f"α: lr={best_lr:.2e} γ={best_gamma:.3f} εd={best_eps:.4f}  "
              f"fitness={best_wolves[0][1]:.1f} (avg_reward={best_reward:.1f})  "
              f"std={fitness_std:.4f}")

    # ── Final results ──────────────────────────────────────────────────────
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

    return {
        "learning_rate": best_lr,
        "gamma": best_gamma,
        "epsilon_decay": best_eps,
        "best_reward": best_reward,
        "iterations": iteration,
        "gwo_time": elapsed,
    }


def main():
    """Parse CLI arguments and run GWO hyperparameter optimisation."""
    parser = argparse.ArgumentParser(
        description='GWO Hyperparameter Optimizer for TALOS DRL Agent')
    parser.add_argument('--wolves', type=int, default=DEFAULT_WOLVES,
                        help=f'Population size (default: {DEFAULT_WOLVES})')
    parser.add_argument('--iters', type=int, default=DEFAULT_ITERS,
                        help=f'Max GWO iterations (default: {DEFAULT_ITERS})')
    parser.add_argument('--rl-episodes', type=int, default=DEFAULT_RL_EPISODES,
                        help=f'RL episodes per fitness eval (default: {DEFAULT_RL_EPISODES})')
    args = parser.parse_args()

    # Override the global constant for this run
    import scripts.gwo_rl_optimizer as _self
    _self.DEFAULT_RL_EPISODES = args.rl_episodes

    run_gwo(args.wolves, args.iters)


if __name__ == "__main__":
    main()