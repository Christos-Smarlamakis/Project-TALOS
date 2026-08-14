# -*- coding: utf-8 -*-
"""
Module: train_agent.py (v1.0)
Project: TALOS v5.9.15
Description:
    Offline training script for the TALOS DRL agent using REAL historical
    paper scores from the SQLite database instead of simulated random scores.

    How offline training works:
    - The agent interacts with TalosEnv as normal (choose API → get reward).
    - Instead of calling _simulate_score() (random numbers), we read the
      overall_score column from the papers table to get real historical
      evaluation scores.
    - This gives the agent a realistic training experience based on actual
      research paper quality distribution.

    Key design decisions:
    - Scores are cached from the database at startup for speed.
    - If the database has no scores (empty), falls back to simulated scores.
    - The agent learns with DDQN (experience replay + target network) for
      500 episodes and saves the trained model.

    Usage:
        python scripts/train_agent.py                          # default 500 episodes
        python scripts/train_agent.py --episodes 1000          # custom count
        python scripts/train_agent.py --episodes 500 --lr 1e-4 --gamma 0.9
"""
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import argparse
import sqlite3
import numpy as np

# ── Add project root to Python's import path ────────────────────────────────
from src.ai.drl.talos_env import TalosEnv
from src.ai.drl.drl_agent import TalosDRLAgent, Transition, DEVICE
from src.ai.drl import drl_agent as da  # For patching hyperparameters

# ── Default training parameters ──────────────────────────────────────────────
DEFAULT_EPISODES = 500
DEFAULT_STEPS = 200
EPS_START = 1.0
EPS_END = 0.01
EPS_DECAY = 0.995


class OfflineTalosEnv(TalosEnv):
    """
    Extension of TalosEnv that uses REAL paper scores from the database.

    Instead of generating random scores via _simulate_score(), this
    environment reads historical overall_score values from the SQLite
    papers table. Each action (API call) samples a random real score
    from the database, giving the agent a realistic training signal.

    If the database is empty or has no scored papers, it falls back
    to the parent class's simulated score generator.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise the offline environment and load scores from the database.

        Args:
            *args: Passed to TalosEnv.__init__().
            **kwargs: Passed to TalosEnv.__init__().
        """
        super().__init__(*args, **kwargs)

        # ── Load real scores from the SQLite database ──────────────────────
        self.real_scores = self._load_scores_from_db()

    @staticmethod
    def _load_scores_from_db():
        """
        Read all overall_score values from the papers table.

        Resolves the database path using the project's profile system.
        Only loads scores that are valid (not NULL, not 0, in range 0-10).

        Returns:
            np.ndarray: Array of real paper scores, or empty array.
        """
        # ── Find the correct database path ─────────────────────────────────
        # We use the same profile-aware logic as DatabaseManager._resolve_profile_db
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))
        profile_dir = os.path.join(project_root, "_profiles")
        active_file = os.path.join(profile_dir, "active_profile.txt")

        db_path = os.path.join(project_root, "talos_research.db")
        if os.path.exists(active_file):
            try:
                with open(active_file, "r", encoding="utf-8") as f:
                    active_profile = f.read().strip()
                profile_db = os.path.join(
                    profile_dir, active_profile, "talos_research.db")
                if os.path.exists(profile_db):
                    db_path = profile_db
            except Exception:
                pass

        # ── Query all scores from the database ─────────────────────────────
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT overall_score FROM papers "
                    "WHERE overall_score IS NOT NULL AND overall_score > 0 "
                    "AND overall_score <= 10"
                )
                rows = cursor.fetchall()
                scores = np.array([row[0] for row in rows], dtype=np.float32)
                return scores
        except sqlite3.Error as e:
            print(f"  WARNING: Could not load scores from DB: {e}")
            return np.array([], dtype=np.float32)

    def _simulate_score(self):
        """
        Return a real historical paper score from the database.

        Randomly samples one score from the array loaded at startup.
        If no scores are available (empty database), falls back to
        the parent class's simulated score generator.

        Returns:
            float: A paper evaluation score between 0 and 10.
        """
        if len(self.real_scores) > 0:
            # ── Sample a random real score ─────────────────────────────────
            # np.random.choice picks uniformly from the array.
            return int(np.random.choice(self.real_scores))
        else:
            # ── Fallback to simulated scores ───────────────────────────────
            return super()._simulate_score()


def main():
    """
    Run the offline DRL training loop using real paper scores.

    For each episode:
    1. Reset the environment (new simulated day).
    2. The agent selects actions using epsilon-greedy.
    3. The environment executes the action, sampling a real paper score
       from the database for the reward.
    4. The experience is stored in replay memory.
    5. The agent learns from past experiences.
    6. After all episodes, save the trained model.
    """
    # ── Parse command-line arguments ───────────────────────────────────────
    parser = argparse.ArgumentParser(
        description='Offline DRL Training with Real Database Scores')
    parser.add_argument('--episodes', type=int, default=DEFAULT_EPISODES,
                        help=f'Number of training episodes (default: {DEFAULT_EPISODES})')
    parser.add_argument('--lr', type=float, default=None,
                        help='Learning rate (default: use drl_agent default)')
    parser.add_argument('--gamma', type=float, default=None,
                        help='Discount factor (default: use drl_agent default)')
    parser.add_argument('--eps-decay', type=float, default=EPS_DECAY,
                        help=f'Epsilon decay per episode (default: {EPS_DECAY})')
    args = parser.parse_args()

    # ── Apply custom hyperparameters if provided ───────────────────────────
    if args.lr is not None:
        da.LR = args.lr
    if args.gamma is not None:
        da.GAMMA = args.gamma

    print("=" * 65)
    print("  TALOS Offline DRL Training — Database-Driven (v5.2.0)")
    print("=" * 65)
    print(f"  Device: {DEVICE}")
    print(f"  Episodes: {args.episodes}")
    print(f"  Max steps/episode: {DEFAULT_STEPS}")
    print(f"  Learning rate: {da.LR:.2e}")
    print(f"  Gamma (discount): {da.GAMMA:.3f}")
    print(f"  Epsilon decay: {args.eps_decay:.4f}")
    print()

    # ── Create the offline environment and RL agent ────────────────────────
    # OfflineTalosEnv loads real scores from the papers table.
    # It now auto-detects all available sources from config.json.
    env = OfflineTalosEnv()
    print(f"  Sources: {len(env.source_names)} ({', '.join(env.source_names[:5])}...)" if len(env.source_names) > 5 else f"  Sources: {len(env.source_names)} ({', '.join(env.source_names)})")
    print(f"  Observation dim: {env.observation_space.shape[0]}")
    print(f"  Action dim: {env.action_space.n}")
    print()

    # Create agent with the exact dimensions from the environment
    agent = TalosDRLAgent(
        state_dim=env.observation_space.shape[0],
        action_dim=env.action_space.n
    )

    # Re-create optimizer if LR was overridden
    if args.lr is not None:
        agent.actor_optimizer = agent.actor_optimizer.__class__(
            agent.actor_online.parameters(), lr=args.lr)

    # ── Report score source ────────────────────────────────────────────────
    if len(env.real_scores) > 0:
        print(f"  Score source: DATABASE ({len(env.real_scores)} real paper scores loaded)")
        print(f"    Score range: {env.real_scores.min():.1f} – {env.real_scores.max():.1f}")
        print(f"    Mean score: {env.real_scores.mean():.1f}")
    else:
        print("  Score source: SIMULATED (no scores found in database)")
    print()

    # ── Initialise training variables ──────────────────────────────────────
    epsilon = EPS_START
    episode_rewards = []
    import time as _time
    train_start = _time.perf_counter()
    last_episode_start = train_start

    # ── Main training loop ─────────────────────────────────────────────────
    for episode in range(1, args.episodes + 1):
        # ── Start a new episode (a new simulated day) ──────────────────────
        obs, _ = env.reset()
        agent.reset_hidden_states()

        total_reward = 0.0

        for step in range(DEFAULT_STEPS):
            # ── Agent selects an action (which API to query) ───────────────
            action = agent.act(obs, epsilon)

            # ── Environment executes the action ────────────────────────────
            # The reward comes from a REAL paper score from the database
            next_obs, reward, terminated, truncated, info = env.step(action)

            # ── Store the experience for later learning ────────────────────
            agent.memory.store(Transition(
                obs, action, reward, next_obs, terminated))

            # ── The agent learns from its past experiences ─────────────────
            # DDQN: sample random batch → compute targets → gradient descent
            agent.learn()

            # ── Advance to the next observation ────────────────────────────
            obs = next_obs
            total_reward += reward

            if terminated or truncated:
                break

        # ── Track reward and decay exploration rate ────────────────────────
        episode_rewards.append(total_reward)
        epsilon = max(EPS_END, epsilon * args.eps_decay)

        # ── Measure episode time ──────────────────────────────────────────
        now = _time.perf_counter()
        ep_time = now - last_episode_start
        last_episode_start = now

        # ── Progress report every episode ──────────────────────────────────
        if episode % 10 == 0 or episode == 1 or episode == args.episodes:
            # Full report every 10 episodes with ETA
            avg_reward = np.mean(episode_rewards[-10:]) if len(episode_rewards) >= 10 else np.mean(episode_rewards)
            remaining = args.episodes - episode
            sec_per_ep = ep_time if episode <= 10 else (now - train_start) / episode
            eta_min = (sec_per_ep * remaining) / 60 if remaining > 0 else 0
            print(f"  Episode {episode:4d}/{args.episodes}  "
                  f"Avg Reward: {avg_reward:8.1f}  "
                  f"{ep_time:.2f}s  ε: {epsilon:.4f}  ETA: {eta_min:.0f}min", flush=True)
        else:
            # Brief line every episode — just episode number and time
            print(f"  Episode {episode:4d}/{args.episodes}  {ep_time:.2f}s", flush=True)

    # ── Save the trained model to disk ─────────────────────────────────────
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'dddqn_trained.pth')

    agent.save(model_path)
    print(f"\n  Model saved: {model_path}")

    # ── Final training summary ─────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  Training Complete")
    print(f"  Best episode reward:  {max(episode_rewards):.1f}")
    print(f"  Average reward (last 50): {np.mean(episode_rewards[-50:]):.1f}")
    print(f"  Total experiences collected: {len(agent.memory)}")
    print(f"  Model saved to: models/dddqn_trained.pth")
    print("=" * 65)


if __name__ == "__main__":
    main()