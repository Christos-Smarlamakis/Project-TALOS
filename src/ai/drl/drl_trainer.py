# -*- coding: utf-8 -*-
"""
Module: drl_trainer.py (v1.3 — Batch 2 TUI hardening)
Project: TALOS v5.3.6
Description:
    Training script for the TALOS Deep Reinforcement Learning agent. Runs
    multiple episodes where the agent interacts with the TalosEnv gymnasium
    environment, learns to select the optimal academic API source using a
    Double Dueling DQN with LSTM network. Saves the trained model to disk.

    v1.3 (Batch 2 TUI audit — presentation layer only, training math untouched):
    - Ctrl+C mid-training no longer dumps a traceback and loses progress:
      the partial model is saved to models/dddqn_partial.pth, a clean
      summary is printed, and the process exits with code 0.
    - Ctrl+C at the interactive episode prompt exits cleanly.
    - Lightweight single-line progress ticker (carriage-return based,
      no external deps) between the every-50-episode summaries.

    Usage:
        python scripts/drl_trainer.py                     # 500 episodes (default)
        python scripts/drl_trainer.py --episodes 1000     # custom count
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

# ── Add project root to Python's import path ────────────────────────────────
# This lets us import core modules from the 'core/' folder
from src.ai.drl.talos_env import TalosEnv
from src.ai.drl.drl_agent import TalosDRLAgent, Transition, DEVICE

# ── Training hyperparameters ─────────────────────────────────────────────────
EPS_START = 1.0        # Initial exploration rate (100% random)
EPS_END = 0.01         # Minimum exploration rate (1% random)
EPS_DECAY = 0.9202     # GWO-optimized epsilon decay
MAX_STEPS = 200        # Max steps per episode (= one simulated day)


def main():
    """
    Run the DRL training loop.

    For each episode:
    1. Reset the environment to get an initial observation.
    2. The agent chooses an action using epsilon-greedy.
    3. The environment executes that action and returns reward + next state.
    4. The experience is stored in replay memory.
    5. The agent learns from a random batch of past experiences.
    6. After all episodes, save the trained model.
    """
    # ── Interactive or CLI episode selection ──────────────────────────────
    episodes = 500  # default
    if "--episodes" in sys.argv:
        # CLI mode: parse the argument
        parser = argparse.ArgumentParser(description='Train TALOS DRL Agent')
        parser.add_argument('--episodes', type=int, default=500,
                            help='Number of training episodes (default: 500)')
        args = parser.parse_args()
        episodes = args.episodes
    else:
        # Interactive mode: ask the user
        try:
            import questionary
            # v1.3: .ask() returns None on Ctrl+C, but some questionary
            # versions re-raise — guard explicitly for a clean exit.
            try:
                choice = questionary.select(
                    "How many training episodes?",
                    choices=[
                        "1. Quick test (50 episodes) ~ 30 sec",
                        "2. Short training (100 episodes) ~ 1 min",
                        "3. Standard training (500 episodes) ~ 5 min",
                        "4. Deep training (1000 episodes) ~ 10 min",
                    ]
                ).ask()
            except KeyboardInterrupt:
                choice = None
            if choice is None:
                print("  Cancelled.")
                return
            episode_map = {"1.": 50, "2.": 100, "3.": 500, "4.": 1000}
            for prefix, count in episode_map.items():
                if choice.startswith(prefix):
                    episodes = count
                    break
        except ImportError:
            # questionary not installed — use default 500
            pass

    print("=" * 60)
    print("  TALOS DRL Training — API Orchestrator Agent")
    print("=" * 60)
    print(f"  Device: {DEVICE}")
    print(f"  Episodes: {episodes}")
    print(f"  Max steps/episode: {MAX_STEPS}")
    print()

    # ── Create environment and agent ───────────────────────────────────────
    env = TalosEnv()
    agent = TalosDRLAgent()

    # ── Epsilon starts high (exploration) and decays over time ─────────────
    epsilon = EPS_START

    # Track total reward across all episodes for progress reporting
    episode_rewards = []

    # ── Models directory (needed for both normal + interrupted saves) ──────
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(models_dir, exist_ok=True)

    # ── Main training loop ─────────────────────────────────────────────────
    # v1.3: wrapped in try/except KeyboardInterrupt — a Ctrl+C mid-training
    # saves the PARTIAL model to dddqn_partial.pth (never clobbering a good
    # dddqn_trained.pth) and exits cleanly with code 0. The loop BODY is
    # byte-identical to v1.2 — no training-math changes.
    interrupted = False
    try:
        for episode in range(1, episodes + 1):
            # Start a fresh episode (new day)
            obs, _ = env.reset()

            # Reset the agent's LSTM hidden states for the new episode
            agent.reset_hidden_states()

            total_reward = 0.0

            for step in range(MAX_STEPS):
                # ── Agent picks an action ──────────────────────────────────
                action = agent.act(obs, epsilon)

                # ── Environment executes the action ────────────────────────
                next_obs, reward, terminated, truncated, info = env.step(action)

                # ── Store the experience in replay memory ─────────────────
                # The agent will learn from this later when it samples batches.
                # v1.2 FIX (time-limit bug): the env now signals episode-end via
                # `truncated` (time limit), NOT `terminated`. We store done=terminated
                # only, so the Bellman target still bootstraps across the artificial
                # 200-step cutoff (avoids biased Q-values near episode end).
                agent.memory.store(Transition(obs, action, reward, next_obs, terminated))

                # ── Agent learns from past experiences ────────────────────
                agent.learn()

                # ── Move to the next state ────────────────────────────────
                obs = next_obs
                total_reward += reward

                if terminated or truncated:
                    break

            # ── Track and print progress ──────────────────────────────────
            episode_rewards.append(total_reward)
            epsilon = max(EPS_END, epsilon * EPS_DECAY)

            # Print every 50 episodes or on the last one
            if episode % 50 == 0 or episode == episodes:
                # Average reward over the last 50 episodes
                avg_reward = np.mean(episode_rewards[-50:])
                # Clear the progress ticker line first, then print summary.
                print(f"\r  Episode {episode:4d}/{episodes}  "
                      f"Avg Reward: {avg_reward:7.1f}  "
                      f"Epsilon: {epsilon:.3f}          ")
            else:
                # v1.3: lightweight single-line ticker (no external deps,
                # resize-safe — never exceeds ~40 chars).
                print(f"\r  Training... episode {episode}/{episodes}",
                      end="", flush=True)
    except KeyboardInterrupt:
        interrupted = True
        completed = len(episode_rewards)
        print(f"\n\n  [STOP] Interrupted at episode {completed}/{episodes}.")
        if completed > 0:
            partial_path = os.path.join(models_dir, 'dddqn_partial.pth')
            agent.save(partial_path)
            print(f"  [SAVE] Partial model saved: {partial_path}")
            print(f"  Avg reward (last 50): {np.mean(episode_rewards[-50:]):.1f}")
        else:
            print("  No episodes completed — nothing to save.")
        print("  Exiting cleanly.")
        sys.exit(0)

    # ── Save the trained model (normal completion) ─────────────────────────
    model_path = os.path.join(models_dir, 'dddqn_trained.pth')
    agent.save(model_path)
    print(f"\n  Model saved: {model_path}")

    # ── Final summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Training Complete")
    print(f"  Best episode reward: {max(episode_rewards):.1f}")
    print(f"  Average reward (last 50): {np.mean(episode_rewards[-50:]):.1f}")
    print("=" * 60)


if __name__ == "__main__":
    # Top-level guard: interrupts outside the training loop (e.g. during
    # env/agent construction) also exit cleanly with code 0.
    try:
        main()
    except KeyboardInterrupt:
        print("\n  [STOP] Interrupted. Exiting cleanly.")
        sys.exit(0)
