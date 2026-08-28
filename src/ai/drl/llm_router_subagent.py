# -*- coding: utf-8 -*-
"""
Module: llm_router_subagent.py
Project: TALOS v5.10.4
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
    - A static ``PROVIDER_PROFILES`` table stores raw SWE-bench Verified scores
      (``swe_bench_score``) plus latency, cost, and rate-limit signals for the
      seven canonical providers (local, nvidia, groq, cerebras, github, gemini,
      deepseek).
    - Quality signals are derived dynamically via relative min-max
      normalization (see the formula below) -- never hardcoded.
    - Prompt length and task type modulate the signals so longer prompts and
      deep-research tasks shift cost/latency/quality trade-offs realistically.
    - ``select_provider`` is constrained to an explicit active-provider list so
      the caller (AIManager) can restrict routing to configured, circuit-closed
      providers only.
    - v5.10.4: provider quality signals can be overridden dynamically via
      refresh_quality_scores(), which reads normalized Q_p scores from the
      Model Discovery Engine (src/ai/llm/model_discovery.py).

    Quality signal normalization (relative min-max):
        Each provider carries a raw benchmark score ``swe_bench_score``. The
        quality signal is computed dynamically as the ratio of the provider's
        raw score to the maximum raw score across all providers::

            Q_p = raw_score(p) / max_k(raw_score(k))

        Consequently, the provider with the top benchmark score receives
        exactly ``Q_p = 1.0``, while every other provider is scaled
        proportionally (``0 < Q_p <= 1.0``). This deterministic, scale-invariant
        mapping is fully traceable for thesis and journal publication.

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
import functools


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

# -- Static provider profiles (raw SWE-bench scores + latency/cost/penalty) -------------------
# swe_bench_score: raw SWE-bench Verified score (higher is better).
# Quality is derived via relative min-max normalization (relative_quality()).
# latency/cost/penalty: higher is worse.
# penalty is the rate-limit penalty incurred by that provider.
# Model-to-provider raw SWE-bench Verified score mapping:
#   nvidia   -- NVIDIA NIM (Nemotron-70B)   -- 70.4  (top anchor, Q_p = 1.0)
#   groq     -- Groq (Llama 3.3 70B)        -- 65.2
#   cerebras -- Cerebras (Llama 3.3 70B)    -- 65.2
#   gemini   -- Gemini 2.5 Pro              -- 63.8
#   deepseek -- DeepSeek                    -- 60.5
#   local    -- Ollama (Qwen 2.5 14B)       -- 55.1
#   github   -- GitHub Models               -- 45.0
#   (fast-edge Neutrino-8B, 42.0, is a dedicated CPU tier; not routed here.)
PROVIDER_PROFILES = {
    "local":    {"swe_bench_score": 55.1, "latency": 0.35, "cost": 0.05, "penalty": 0.05},
    "nvidia":   {"swe_bench_score": 70.4, "latency": 0.30, "cost": 0.45, "penalty": 0.25},
    "groq":     {"swe_bench_score": 65.2, "latency": 0.10, "cost": 0.30, "penalty": 0.30},
    "cerebras": {"swe_bench_score": 65.2, "latency": 0.12, "cost": 0.35, "penalty": 0.28},
    "github":   {"swe_bench_score": 45.0, "latency": 0.40, "cost": 0.20, "penalty": 0.35},
    "gemini":   {"swe_bench_score": 63.8, "latency": 0.45, "cost": 0.40, "penalty": 0.40},
    "deepseek": {"swe_bench_score": 60.5, "latency": 0.50, "cost": 0.25, "penalty": 0.35},
}

# -- Relative min-max normalization denominator --------------------------------
# The maximum raw SWE-bench score anchors the quality normalization so the top
# provider receives exactly QualityScore = 1.0.
MAX_SWE_BENCH_SCORE = float(max(
    profile["swe_bench_score"] for profile in PROVIDER_PROFILES.values()
))


@functools.lru_cache(maxsize=32)
def relative_quality(raw_score):
    """Normalize a raw benchmark score to a relative quality in [0, 1].

    Implements dynamic relative min-max normalization::

        Q_p = raw_score(p) / max_k(raw_score(k))

    The provider holding the top benchmark score therefore maps to exactly 1.0,
    while every other provider is scaled proportionally to its raw score.

    Args:
        raw_score (float): Raw SWE-bench Verified score for a provider.

    Returns:
        float: Relative quality signal in [0, 1].
    """
    if MAX_SWE_BENCH_SCORE <= 0.0:
        return 0.0
    return float(raw_score) / MAX_SWE_BENCH_SCORE

# -- Task-type modifiers: prompt-length scale and quality bias ---------------
# deep_research favors longer, higher-quality prompts; fast_screening favors
# short, low-latency prompts; air_gapped_local maps to local-friendly routing.
TASK_MODIFIERS = {
    "deep_research":    {"prompt_scale": 1.4, "quality_bias": 0.05},
    "fast_screening":   {"prompt_scale": 0.6, "quality_bias": -0.02},
    "foraging_evaluation": {"prompt_scale": 1.0, "quality_bias": 0.02},
    "air_gapped_local": {"prompt_scale": 0.8, "quality_bias": 0.00},
    "default":          {"prompt_scale": 1.0, "quality_bias": 0.00},
}


@functools.lru_cache(maxsize=4096)
def estimate_prompt_tokens(text):
    """Approximate the token length of a prompt from its character count.

    Uses the common four-characters-per-token heuristic, which is conservative
    for scientific abstracts and structured prompts.

    Args:
        text (str): The prompt text.

    Returns:
        int: Estimated token count (minimum 1).
    """
    if not text:
        return 1
    return max(1, int(len(str(text)) / 4))


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
        # -- v5.10.4: dynamic quality overrides from the Model Discovery Engine --
        # Empty by default so the static PROVIDER_PROFILES normalization is
        # used unless refresh_quality_scores() is called explicitly.
        self._quality_overrides = {}

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

        The quality signal is derived dynamically via relative min-max
        normalization (``relative_quality``): ``Q_p = raw / max(raw)``.

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
            base_quality = self._quality_overrides.get(
                name, relative_quality(profile["swe_bench_score"])
            )
            quality = float(np.clip(
                base_quality + modifier["quality_bias"],
                0.0, 1.0
            ))
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


    def load_quality_scores(self, quality_map):
        """Override provider quality signals from an external quality map.

        Args:
            quality_map (dict[str, float] | None): Mapping of provider name to
                normalized quality score Q_p in [0, 1]. None clears overrides.

        Returns:
            LLMRouterSubAgent: self, for chaining.
        """
        self._quality_overrides = {} if quality_map is None else dict(quality_map)
        return self

    def refresh_quality_scores(self, engine=None, online=None):
        """Refresh provider quality signals from the Model Discovery Engine.

        Lazily imports the engine and reads its provider-level normalized
        quality scores (Q_p). This is best-effort: on any failure the static
        PROVIDER_PROFILES normalization remains in effect.

        Args:
            engine (ModelDiscoveryEngine | None): Injectable engine for testing.
                When None, a fresh engine is created lazily.
            online (bool | None): Online discovery flag. When None, the engine
                default (offline, air-gapped) is used.

        Returns:
            dict[str, float]: The refreshed quality override map (may be empty).
        """
        if engine is None:
            try:
                from src.ai.llm.model_discovery import ModelDiscoveryEngine
                engine = ModelDiscoveryEngine()
            except Exception:
                return dict(self._quality_overrides)
        try:
            quality_map = engine.get_provider_quality_scores(online=online)
            self._quality_overrides = dict(quality_map)
        except Exception:
            pass
        return dict(self._quality_overrides)

    def _emit_router_decision(self, provider, task_type, prompt_length, score):
        """Emit a non-blocking router_decision Synapse event (best-effort).

        Args:
            provider (str): The selected provider name.
            task_type (str): The routing task type.
            prompt_length (int): The estimated prompt length in tokens.
            score (float): The shaped reward score of the selected provider.

        Returns:
            None: Emission is best-effort and never raises.
        """
        try:
            from src.integration.synapse_client import synapse_emitter
            synapse_emitter.emit("router_decision", {
                "provider": provider,
                "task_type": task_type,
                "prompt_length": int(prompt_length or 0),
                "score": float(score),
            })
        except Exception:
            pass


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
        if best_provider is not None:
            self._emit_router_decision(best_provider, task_type, prompt_length, best_score)
        return best_provider

