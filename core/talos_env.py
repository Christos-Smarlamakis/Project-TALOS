# -*- coding: utf-8 -*-
"""
Module: talos_env.py (v1.0)
Project: TALOS v5.0.0
Description:
    Gymnasium reinforcement learning environment for TALOS API source selection.
    Models the problem of choosing which academic API to query next (ArXiv,
    OpenAlex, or Semantic Scholar) based on daily call limits, recent success
    rates, and time of day. A "Sleep" action lets the agent rest when limits
    are nearly exhausted, conserving API quotas for the next day.

    Key design decisions:
    - Observation space is a 6-element flat array (not an image) because the
      state is small and fully observable — no need for CNNs.
    - Reward function heavily penalizes API errors (-50) to teach the agent
      to avoid rate-limit violations.
    - Sleep action is rewarded (+2) only when limits are near max, so the
      agent learns to rest strategically, not just sleep all the time.
    - All values are normalized (0.0-1.0) for stable neural network training.
"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces

# ── Hour of day → normalized 0.0-1.0 ────────────────────────────────────────
# We divide current hour (0-23) by 23 to get a 0.0-1.0 range.
# This helps the agent understand "time of day" — some hours are busier.

# ── API daily limits (realistic defaults for free tiers) ─────────────────────
DEFAULT_ARXIV_LIMIT = 100
DEFAULT_OPENALEX_LIMIT = 100
DEFAULT_S2_LIMIT = 100


class TalosEnv(gym.Env):
    """
    Gymnasium environment for TALOS API source selection.

    The agent must choose which academic API to query next from three sources
    plus a "sleep" option. Each API has a daily call limit. The agent receives
    a score (0-10) after each query, and must learn to manage its limited
    API calls to maximize total score over time.

    Attributes:
        arxiv_limit (int): Maximum ArXiv calls allowed per day.
        openalex_limit (int): Maximum OpenAlex calls per day.
        s2_limit (int): Maximum Semantic Scholar calls per day.
        arxiv_calls (int): ArXiv calls made so far this episode.
        openalex_calls (int): OpenAlex calls made so far this episode.
        s2_calls (int): Semantic Scholar calls made so far this episode.
        total_score (float): Running sum of scores received this episode.
        current_step (int): Step counter for the current episode.
    """

    def __init__(self, arxiv_limit=100, openalex_limit=100, s2_limit=100):
        """
        Initialize the environment with per-API daily limits.

        Args:
            arxiv_limit (int): Max ArXiv queries per day.
            openalex_limit (int): Max OpenAlex queries per day.
            s2_limit (int): Max Semantic Scholar queries per day.
        """
        super().__init__()

        # ── Store API limits ───────────────────────────────────────────────
        self.arxiv_limit = arxiv_limit
        self.openalex_limit = openalex_limit
        self.s2_limit = s2_limit

        # ── 6-element observation vector (all values 0.0–1.0) ───────────────
        # Index 0: normalized hour (0.0 = midnight, 1.0 = 23:00)
        # Index 1: arxiv calls / arxiv limit
        # Index 2: openalex calls / openalex limit
        # Index 3: semanticscholar calls / s2 limit
        # Index 4: consecutive low scores / 10.0
        # Index 5: consecutive errors / 10.0
        low = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        high = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        # ── 4 possible actions ──────────────────────────────────────────────
        # 0 = Query ArXiv
        # 1 = Query OpenAlex
        # 2 = Query Semantic Scholar
        # 3 = Sleep (cooldown, wait until next time step)
        self.action_space = spaces.Discrete(4)

    def reset(self, seed=None, options=None):
        """
        Reset the environment to start a new episode (a new "day").

        All API call counters go back to zero. The hour is randomized.
        Step counter resets. Returns the initial observation.

        Args:
            seed (int, optional): Random seed for reproducibility.
            options (dict, optional): Additional reset options (unused).

        Returns:
            tuple: (observation, info_dict)
        """
        # ── Seed the random number generator if requested ──────────────────
        super().reset(seed=seed)

        # ── Reset all counters to zero ──────────────────────────────────────
        self.arxiv_calls = 0
        self.openalex_calls = 0
        self.s2_calls = 0

        # These track patterns in the agent's recent performance
        # so it can learn to stop choosing bad sources.
        self.consecutive_low_scores = 0  # How many queries in a row scored < 7
        self.consecutive_errors = 0      # How many queries in a row got API errors

        # ── Running score for this episode ──────────────────────────────────
        self.total_score = 0.0

        # ── Step counter (episode ends at 200 steps by default) ─────────────
        self.current_step = 0

        # ── Pick a random starting hour (0-23) ──────────────────────────────
        self.current_hour = np.random.randint(0, 24)

        # ── Build the initial observation ───────────────────────────────────
        obs = self._build_obs()
        info = {"hour": self.current_hour}
        return obs, info

    def step(self, action):
        """
        Execute one action (choose an API or sleep) and return the result.

        The environment simulates the outcome of querying an API:
        - If the API is over its daily limit, the call fails with an error.
        - Otherwise, a random score is generated (weighted towards higher
          scores for demonstration; in production, real scores from the
          TALOS pipeline would be fed in).

        Args:
            action (int): 0=ArXiv, 1=OpenAlex, 2=SemanticScholar, 3=Sleep.

        Returns:
            tuple: (observation, reward, terminated, truncated, info)
                observation (np.ndarray): 6-element observation vector.
                reward (float): Reward for this step.
                terminated (bool): True if episode is over (max steps).
                truncated (bool): Always False in this implementation.
                info (dict): Diagnostics dictionary with 'action' and 'score'.
        """
        self.current_step += 1
        reward = 0.0
        score = 0  # The hypothetical LLM score (0-10)

        # ── Action 3: SLEEP / COOLDOWN ──────────────────────────────────────
        if action == 3:
            # The agent chooses to wait. This is a strategic pause to avoid
            # hitting rate limits. We reward sleep ONLY if limits are near max.
            used_ratio = max(
                self.arxiv_calls / self.arxiv_limit,
                self.openalex_calls / self.openalex_limit,
                self.s2_calls / self.s2_limit
            )
            if used_ratio > 0.8:
                reward = 2.0  # Smart sleep — limits are nearly exhausted

        # ── Action 0: ARXIV ─────────────────────────────────────────────────
        elif action == 0:
            if self.arxiv_calls >= self.arxiv_limit:
                # Limit exceeded → this is an error (rate limit hit)
                reward = -50.0
                self.consecutive_errors += 1
                self.consecutive_low_scores = 0
            else:
                self.arxiv_calls += 1
                # Simulate a score. In production, a real LLM evaluator would
                # provide the actual score for the retrieved paper.
                score = self._simulate_score()
                reward = self._score_to_reward(score)
                # Track patterns
                if score < 7:
                    self.consecutive_low_scores += 1
                else:
                    self.consecutive_low_scores = 0
                self.consecutive_errors = 0

        # ── Action 1: OPENALEX ──────────────────────────────────────────────
        elif action == 1:
            if self.openalex_calls >= self.openalex_limit:
                reward = -50.0
                self.consecutive_errors += 1
                self.consecutive_low_scores = 0
            else:
                self.openalex_calls += 1
                score = self._simulate_score()
                reward = self._score_to_reward(score)
                if score < 7:
                    self.consecutive_low_scores += 1
                else:
                    self.consecutive_low_scores = 0
                self.consecutive_errors = 0

        # ── Action 2: SEMANTIC SCHOLAR ──────────────────────────────────────
        elif action == 2:
            if self.s2_calls >= self.s2_limit:
                reward = -50.0
                self.consecutive_errors += 1
                self.consecutive_low_scores = 0
            else:
                self.s2_calls += 1
                score = self._simulate_score()
                reward = self._score_to_reward(score)
                if score < 7:
                    self.consecutive_low_scores += 1
                else:
                    self.consecutive_low_scores = 0
                self.consecutive_errors = 0

        # ── Accumulate score ────────────────────────────────────────────────
        self.total_score += score if score else 0

        # ── Advance time ────────────────────────────────────────────────────
        # Each successful API call takes some time. We move the hour forward
        # slightly after a non-sleep action.
        if action != 3:
            self.current_hour = (self.current_hour + 1) % 24

        # ── Cap consecutive counters at 10 (for normalized observation) ─────
        self.consecutive_low_scores = min(self.consecutive_low_scores, 10)
        self.consecutive_errors = min(self.consecutive_errors, 10)

        # ── Episode termination ─────────────────────────────────────────────
        # End the episode after 200 steps (a simulated "day").
        terminated = self.current_step >= 200
        truncated = False

        # ── Build next observation ──────────────────────────────────────────
        obs = self._build_obs()
        info = {"action": int(action), "score": score}

        return obs, reward, terminated, truncated, info

    def _build_obs(self):
        """
        Construct the normalized observation vector from current state.

        All six values are in the range [0.0, 1.0] to help the neural
        network converge faster.

        Returns:
            np.ndarray: Shape (6,) float32 array.
        """
        return np.array([
            self.current_hour / 23.0,                          # Normalized hour
            self.arxiv_calls / self.arxiv_limit,               # ArXiv usage ratio
            self.openalex_calls / self.openalex_limit,         # OpenAlex usage ratio
            self.s2_calls / self.s2_limit,                     # S2 usage ratio
            self.consecutive_low_scores / 10.0,                # Low score streak
            self.consecutive_errors / 10.0,                    # Error streak
        ], dtype=np.float32)

    def _simulate_score(self):
        """
        Generate a simulated LLM evaluation score (0-10).

        The distribution is weighted towards higher scores so the agent
        can learn to find good papers. In production, this would be
        replaced by actual TALOS evaluation pipeline results.

        Returns:
            int: Score between 0 and 10.
        """
        # Weighted random choice: 20% chance of score 5-6, 40% of 7-8, 40% of 9-10
        roll = np.random.random()
        if roll < 0.2:
            return np.random.randint(5, 7)   # 5 or 6
        elif roll < 0.6:
            return np.random.randint(7, 9)   # 7 or 8
        else:
            return np.random.randint(9, 11)  # 9 or 10

    @staticmethod
    def _score_to_reward(score):
        """
        Convert a paper score (0-10) into a reinforcement learning reward.

        The mapping encourages the agent to prioritize high-scoring papers:
        - +20 for elite papers (8-10)
        - +5 for decent papers (7)
        - -10 for low-quality papers (<7)

        Args:
            score (int): Paper evaluation score.

        Returns:
            float: RL reward value.
        """
        if score >= 8:
            return 20.0
        elif score == 7:
            return 5.0
        else:
            return -10.0