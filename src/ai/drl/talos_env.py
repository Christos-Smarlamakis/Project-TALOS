# -*- coding: utf-8 -*-
"""
Module: talos_env.py (v3.1 — Time-limit truncation fix)
Project: TALOS v5.10.0
Description:
    Gymnasium reinforcement learning environment for TALOS API source selection.
    Supports ALL 14 academic sources dynamically (not just the original 3).
    The agent chooses which API to query next from N sources plus a "sleep"
    option. Each source has a daily call limit read from config.json.

    How it works:
    - On init, reads the list of sources from a well-known config key
      ("source_names") or auto-detects them from config keys ending in "_query".
    - For each source, reads its per-day API limit from config (defaults to 100).
    - Action indices 0..N-1 correspond to the N sources.
    - Action N is the sleep/cooldown action.
    - Observation vector: [hour/23, usage_ratio_0, ..., usage_ratio_N-1,
      low_score_streak/10, error_streak/10] — fully dynamic.

    Key design decisions:
    - All source state is stored in parallel numpy arrays (calls, limits) so
      the step() method is a clean for-loop over action indices, not a
      massive if/elif chain.
    - Backward compatible: if no source_names config exists, falls back to the
      original 3-source behaviour (ArXiv, OpenAlex, Semantic Scholar).
    - Reward function is unchanged: +20 for elite (≥8), +5 for decent (7),
      -10 for low (<7), -50 for rate-limit errors, +2 for smart sleep.
    - All values normalized to 0.0–1.0 for stable neural network training.
"""
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import json
import numpy as np
import gymnasium as gym
from gymnasium import spaces

# ── Default API limit when config doesn't specify one ────────────────────────
DEFAULT_SOURCE_LIMIT = 100

# ── Known 14-source list (used as fallback when config doesn't define them) ───
ALL_KNOWN_SOURCES = [
    "arxiv", "openalex", "semantic_scholar", "crossref", "dblp",
    "pubmed", "plos", "core", "osti", "scigov",
    "openarchives", "ieee", "elsevier", "springer",
]

# ── Provider names for observation vector (v3.0 — Provider-Aware) ─────────────
_PROVIDER_NAMES = ["gemini", "deepseek", "huggingface", "local"]
_PROVIDER_COUNT = len(_PROVIDER_NAMES)


def _load_source_list(config=None):
    """
    Read the ordered list of source names from config.json.

    Strategy (in priority order):
      1. Look for a "source_names" key in config (explicit list).
      2. Auto-detect: scan all config keys ending in "_query", extract the
         source name before "_query", and sort alphabetically for determinism.
      3. If neither works (no config file at all), return the 3 original sources.

    Args:
        config (dict, optional): Loaded config.json as a dict.

    Returns:
        list of str: Ordered source names (e.g. ["arxiv", "core", ...]).
    """
    if config is None:
        config = _try_load_config()

    # ── Explicit source_names list ───────────────────────────────────────────
    if config and "source_names" in config:
        return list(config["source_names"])

    # ── Auto-detect from _query keys ────────────────────────────────────────
    if config:
        detected = sorted([
            k.replace("_query", "")
            for k in config.keys()
            if k.endswith("_query") and k != "query_translator_prompt"
        ])
        if detected:
            return detected

    # ── Fallback to the original 3 sources ──────────────────────────────────
    return ["arxiv", "openalex", "semantic_scholar"]


def _try_load_config():
    """
    Attempt to load config.json from the project root.

    Returns:
        dict or None: The loaded config, or None if the file is missing.
    """
    project_root = _P if _P else os.getcwd()
    config_path = os.path.join(project_root, "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(project_root, "config.template.json")
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _load_source_limits(source_names, config=None):
    """
    Read the per-source API call limits from config.json.

    Looks for keys like "arxiv_limit", "openalex_limit", etc.
    If a source has no limit defined, uses DEFAULT_SOURCE_LIMIT (100).

    Args:
        source_names (list of str): Ordered source names (e.g. ["arxiv", ...]).
        config (dict, optional): Loaded config.json.

    Returns:
        np.ndarray: Array of limits, one per source (shape (N,)).
    """
    if config is None:
        config = _try_load_config()
    limits = []
    for name in source_names:
        key = f"{name}_limit"
        limit = config.get(key, DEFAULT_SOURCE_LIMIT) if config else DEFAULT_SOURCE_LIMIT
        limits.append(int(limit))
    return np.array(limits, dtype=np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
class TalosEnv(gym.Env):
    """
    Gymnasium environment for TALOS API source selection (N sources + sleep).

    Supports ALL available academic APIs dynamically.  Each source has a
    daily call limit.  The agent receives a score (0-10) after each query
    and must learn to manage its limited API calls across all sources to
    maximize total score over time.

    Attributes:
        source_names (list of str): Ordered source names.
        num_sources (int): Number of API sources (N).
        source_limits (np.ndarray): Daily call limit per source (shape (N,)).
        source_calls (np.ndarray): Calls made so far this episode (shape (N,)).
        total_score (float): Running sum of scores received this episode.
        current_step (int): Step counter for the current episode.
        consecutive_low_scores (int): How many queries in a row scored < 7.
        consecutive_errors (int): How many queries in a row got API errors.
        current_hour (int): Simulated hour (0-23).
    """

    def __init__(self, source_names=None, source_limits=None, config=None):
        """
        Initialize the environment with N dynamic sources + sleep action.

        Args:
            source_names (list of str, optional): Ordered list of source names.
                If None, auto-detected from config.json.
            source_limits (list or np.ndarray, optional): Per-source limits.
                If None, read from config.json or default to 100.
            config (dict, optional): Pre-loaded config.json. If None, auto-loaded.
        """
        super().__init__()

        # ── Resolve config ───────────────────────────────────────────────────
        if config is None:
            config = _try_load_config()
        self.config = config

        # ── Resolve source list ──────────────────────────────────────────────
        if source_names is None:
            source_names = _load_source_list(config)
        # Deduplicate while preserving order
        seen = set()
        self.source_names = []
        for n in source_names:
            if n not in seen:
                self.source_names.append(n)
                seen.add(n)
        self.num_sources = len(self.source_names)

        # ── Resolve per-source limits ────────────────────────────────────────
        if source_limits is not None:
            self.source_limits = np.array(source_limits, dtype=np.float32)
            # Pad or truncate to match num_sources
            if len(self.source_limits) < self.num_sources:
                pad = np.full(self.num_sources - len(self.source_limits),
                              DEFAULT_SOURCE_LIMIT, dtype=np.float32)
                self.source_limits = np.concatenate([self.source_limits, pad])
            else:
                self.source_limits = self.source_limits[:self.num_sources]
        else:
            self.source_limits = _load_source_limits(self.source_names, config)

        # ── Build observation space dynamically ──────────────────────────────
        # Structure: [hour/24, usage_ratio_0, ..., usage_ratio_N-1,
        #             low_score_streak/10, error_streak/10,
        #             provider_ratio_0, ..., provider_ratio_3]
        # Total size = 1 (hour) + N (sources) + 2 (patterns) + 4 (providers)
        obs_size = 1 + self.num_sources + 2 + _PROVIDER_COUNT
        low = np.zeros(obs_size, dtype=np.float32)
        high = np.ones(obs_size, dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        # ── Action space: N sources (indices 0..N-1) + 1 sleep (index N) ────
        self.action_space = spaces.Discrete(self.num_sources + 1)
        # Convenience attribute: sleep action index = num_sources
        self.SLEEP_ACTION = self.num_sources

    # ── Public properties for external code that references old names ────────
    @property
    def arxiv_limit(self):
        """Backward-compat: return limit for 'arxiv' if it exists."""
        return self._get_limit("arxiv")

    @property
    def openalex_limit(self):
        """Backward-compat: return limit for 'openalex' if it exists."""
        return self._get_limit("openalex")

    @property
    def s2_limit(self):
        """Backward-compat: return limit for 'semantic_scholar' if it exists."""
        return self._get_limit("semantic_scholar")

    def _get_limit(self, name):
        """Get the limit for a named source, or DEFAULT_SOURCE_LIMIT."""
        try:
            idx = self.source_names.index(name)
            return int(self.source_limits[idx])
        except ValueError:
            return DEFAULT_SOURCE_LIMIT

    def reset(self, seed=None, options=None):
        """
        Reset the environment to start a new episode (a new "day").

        All per-source call counters go back to zero. The hour is randomized.
        Step counter and pattern trackers reset.

        Args:
            seed (int, optional): Random seed for reproducibility.
            options (dict, optional): Additional reset options (unused).

        Returns:
            tuple: (observation, info_dict)
        """
        # ── Seed the random number generator if requested ──────────────────
        super().reset(seed=seed)

        # ── Reset all source call counters to zero ──────────────────────────
        self.source_calls = np.zeros(self.num_sources, dtype=np.float32)

        # ── Reset pattern trackers ──────────────────────────────────────────
        self.consecutive_low_scores = 0
        self.consecutive_errors = 0

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
        Execute one action (choose a source index or sleep) and return result.

        Actions 0..N-1 query source_names[action].
        Action N (SLEEP_ACTION) is the cooldown/sleep action.

        The environment simulates querying an API:
        - If the source is over its daily limit, the action fails (penalty).
        - Otherwise, a score is sampled (simulated or real) and converted
          to a reward.

        Args:
            action (int): 0..N-1 = query source, N = sleep.

        Returns:
            tuple: (observation, reward, terminated, truncated, info)
                observation (np.ndarray): Dynamic observation vector.
                reward (float): Reward for this step.
                terminated (bool): True if episode is over (max steps).
                truncated (bool): Always False.
                info (dict): {'action', 'source', 'score'}.
        """
        self.current_step += 1
        reward = 0.0
        score = 0
        source_name = "sleep"

        # ═══════════════════════════════════════════════════════════════════
        # SLEEP / COOLDOWN (action = self.SLEEP_ACTION)
        # ═══════════════════════════════════════════════════════════════════
        if action == self.SLEEP_ACTION:
            # Reward sleep only when limits are near exhaustion
            if self.num_sources > 0:
                used_ratios = self.source_calls / np.maximum(self.source_limits, 1.0)
                max_ratio = float(np.max(used_ratios))
                if max_ratio > 0.8:
                    reward = 2.0  # Smart sleep — limits are nearly exhausted

        # ═══════════════════════════════════════════════════════════════════
        # QUERY A SOURCE (action 0..N-1)
        # ═══════════════════════════════════════════════════════════════════
        elif 0 <= action < self.num_sources:
            source_name = self.source_names[action]
            limit = int(self.source_limits[action])
            current_calls = int(self.source_calls[action])

            if current_calls >= limit:
                # ── Rate limit hit — strong penalty ────────────────────────
                reward = -50.0
                self.consecutive_errors += 1
                self.consecutive_low_scores = 0
            else:
                # ── Execute the query ──────────────────────────────────────
                self.source_calls[action] += 1
                score = self._simulate_score()
                reward = self._score_to_reward(score)
                # Track patterns for observation
                if score < 7:
                    self.consecutive_low_scores += 1
                else:
                    self.consecutive_low_scores = 0
                self.consecutive_errors = 0

        # ── Accumulate score ────────────────────────────────────────────────
        self.total_score += score if score else 0

        # ── Advance time (one hour per non-sleep action) ─────────────────────
        if action != self.SLEEP_ACTION:
            self.current_hour = (self.current_hour + 1) % 24

        # ── Cap consecutive counters at 10 (for normalized observation) ─────
        self.consecutive_low_scores = min(self.consecutive_low_scores, 10)
        self.consecutive_errors = min(self.consecutive_errors, 10)

        # ── Episode termination ─────────────────────────────────────────────
        # v3.1 FIX (time-limit bug): the 200-step cutoff is a TIME LIMIT, not
        # a true terminal state. Per Gymnasium semantics it must be reported
        # as `truncated`, so training code bootstraps the Bellman target
        # across the cutoff (done=False in replay memory). Reporting it as
        # `terminated` biased Q-values near episode end.
        terminated = False
        truncated = self.current_step >= 200

        # ── Build next observation ──────────────────────────────────────────
        obs = self._build_obs()
        info = {"action": int(action), "source": source_name, "score": score}

        return obs, reward, terminated, truncated, info

    def _build_obs(self):
        """
        Construct the normalized observation vector from current state.

        Structure:
            [0]           hour / 23.0  (0.0–1.0)
            [1 .. N]       usage ratio per source (calls/limit, 0.0–1.0)
            [N+1]          consecutive_low_scores / 10.0
            [N+2]          consecutive_errors / 10.0

        Returns:
            np.ndarray: Shape (1 + num_sources + 2,) float32 array.
        """
        # ── Usage ratios: calls / limit, safe-division ──────────────────────
        ratios = self.source_calls / np.maximum(self.source_limits, 1.0)

        # ── Assemble vector (v3.0 — includes 4 provider zeros during training) ─
        # During training, provider ratios are simulated (all zeros for now).
        # The live orchestrator fills real provider values at inference time.
        provider_zeros = np.zeros(_PROVIDER_COUNT, dtype=np.float32)
        obs = np.concatenate([
            np.array([self.current_hour / 24.0], dtype=np.float32),
            ratios.astype(np.float32),
            np.array([
                self.consecutive_low_scores / 10.0,
                self.consecutive_errors / 10.0,
            ], dtype=np.float32),
            provider_zeros,
        ])
        return obs

    def _simulate_score(self):
        """
        Generate a simulated LLM evaluation score (0-10).

        The distribution is weighted towards higher scores so the agent
        can learn to find good papers. In production, this should be
        replaced by real TALOS pipeline scores (see OfflineTalosEnv subclass
        in scripts/train_agent.py).

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


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL CONSTANTS (exported for drl_agent.py to reference)
# ═══════════════════════════════════════════════════════════════════════════════

def get_default_state_space():
    """
    Return the STATE_SPACE size for the default auto-detected source count.

    v3.0: Includes 4 provider ratios in the observation vector.

    Returns:
        int: Default observation vector length (1 + num_sources + 2 + 4).
    """
    names = _load_source_list()
    return 1 + len(names) + 2 + _PROVIDER_COUNT


def get_default_action_space():
    """
    Return the ACTION_SPACE size for the default auto-detected source count.

    Returns:
        int: Default number of actions (num_sources + 1 sleep).
    """
    names = _load_source_list()
    return len(names) + 1