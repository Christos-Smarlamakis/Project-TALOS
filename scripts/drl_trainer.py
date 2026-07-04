# -*- coding: utf-8 -*-
"""
Module: drl_trainer.py (v1.0)
Project: TALOS v5.0.0
Description:
    Training script for the TALOS Deep Reinforcement Learning agent. Runs
    multiple episodes where the agent interacts with the TalosEnv gymnasium
    environment, learns to select the optimal academic API source using a
    Double Dueling DQN with LSTM network. Saves the trained model to disk.

    Usage:
        python scripts/drl_trainer.py                     # 500 episodes (default)
        python scripts/drl_trainer.py --episodes 1000     # custom count
"""
import os
import sys
import argparse
import numpy as np

# ── Add project root to Python's import path ────────────────────────────────
# This lets us import core modules from the 'core/' folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.talos_env import TalosEnv
from core.drl_agent import TalosDRLAgent, Transition, DEVICE

# ── Training hyperparameters ─────────────────────────────────────────────────
EPS_START = 1.0        # Initial exploration rate (100% random)
EPS_END = 0.01         # Minimum exploration rate (1% random)
EPS_DECAY = 0.9415     # GWO-optimized epsilon decay
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
            choice = questionary.select(
                "How many training episodes?",
                choices=[
                    "1. Quick test (50 episodes) ~ 30 sec",
                    "2. Short training (100 episodes) ~ 1 min",
                    "3. Standard training (500 episodes) ~ 5 min",
                    "4. Deep training (1000 episodes) ~ 10 min",
                ]
            ).ask()
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
    print(f"  Episodes: {args.episodes}")
    print(f"  Max steps/episode: {MAX_STEPS}")
    print()

    # ── Create environment and agent ───────────────────────────────────────
    env = TalosEnv()
    agent = TalosDRLAgent()

    # ── Epsilon starts high (exploration) and decays over time ─────────────
    epsilon = EPS_START

    # Track total reward across all episodes for progress reporting
    episode_rewards = []

    # ── Main training loop ─────────────────────────────────────────────────
    for episode in range(1, args.episodes + 1):
        # Start a fresh episode (new day)
        obs, _ = env.reset()

        # Reset the agent's LSTM hidden states for the new episode
        agent.reset_hidden_states()

        total_reward = 0.0

        for step in range(MAX_STEPS):
            # ── Agent picks an action ──────────────────────────────────────
            action = agent.act(obs, epsilon)

            # ── Environment executes the action ────────────────────────────
            next_obs, reward, terminated, truncated, info = env.step(action)

            # ── Store the experience in replay memory ─────────────────────
            # The agent will learn from this later when it samples batches
            agent.memory.store(Transition(obs, action, reward, next_obs, terminated))

            # ── Agent learns from past experiences ────────────────────────
            agent.learn()

            # ── Move to the next state ────────────────────────────────────
            obs = next_obs
            total_reward += reward

            if terminated or truncated:
                break

        # ── Track and print progress ──────────────────────────────────────
        episode_rewards.append(total_reward)
        epsilon = max(EPS_END, epsilon * EPS_DECAY)

        # Print every 50 episodes or on the last one
        if episode % 50 == 0 or episode == args.episodes:
            # Average reward over the last 50 episodes
            avg_reward = np.mean(episode_rewards[-50:])
            print(f"  Episode {episode:4d}/{args.episodes}  "
                  f"Avg Reward: {avg_reward:7.1f}  "
                  f"Epsilon: {epsilon:.3f}")

    # ── Save the trained model ─────────────────────────────────────────────
    # Create the models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(models_dir, exist_ok=True)
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
    main()