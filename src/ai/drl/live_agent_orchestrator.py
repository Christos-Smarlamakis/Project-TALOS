# -*- coding: utf-8 -*-
"""
Module: live_agent_orchestrator.py (v1.1 — Batch 1 audit fixes)
Project: TALOS v5.9.18
Description:
    Main orchestration loop for the TALOS Live DRL Agent. Handles the
    full cycle: state calculation → action selection → API fetch →
    AI evaluation → reward calculation → counter updates.

    Extracted from talos_live_agent.py v2.1 to enable reuse across
    the live agent and the 24/7 daemon (talos_service.py).

    NEW in v1.0: Provider-aware state tracking. The observation vector
    now includes per-provider usage ratios (gemini, deepseek, huggingface,
    local) so the DRL agent can learn to respect provider rate limits.

    Key design decisions:
    - Epsilon=0.0 (pure exploitation) during live inference.
    - Each iteration makes EXACTLY ONE API call + AI evaluation.
    - Provider limits are read from config.json (tier-based for Gemini).
    - Throttle of 5 seconds between API calls.
    - Sleep action resets all counters (new "day").
"""
import os
import sys
import json
import time
import requests
import numpy as np
from datetime import datetime

# ── Configuration constants ──────────────────────────────────────────────────
MAX_CALLS_PER_SOURCE = 100      # Default API call limit per source per "day"
SCORE_THRESHOLD_HIGH = 8         # Score ≥ 8 → high reward
SCORE_THRESHOLD_MEDIUM = 7       # Score ≥ 7 → medium reward
REWARD_HIGH = 20                 # +20 for high-scoring papers
REWARD_MEDIUM = 5                # +5 for medium-scoring papers
REWARD_LOW = -10                 # -10 for low-scoring papers
REWARD_ERROR = -50               # -50 for API errors (429, 402, etc.)
SLEEP_SECONDS = 3600             # 1 hour sleep for the sleep action
THROTTLE_SECONDS = 5             # Mandatory cooldown between API calls
# v1.1 FIX (train/inference distribution mismatch): the training env
# (talos_env._build_obs) normalizes streaks by /10. Inference MUST use the
# same divisor, otherwise the agent sees streak features compressed 2x
# relative to what it was trained on (silent domain shift).
LOW_SCORE_MAX = 10               # Streak normalization divisor — MUST match talos_env (=10)
PROVIDER_MAX_CALLS_FREE = 100    # Default daily provider calls (free tier)

# ── Provider names for state tracking ────────────────────────────────────────
_PROVIDER_NAMES = ["gemini", "deepseek", "huggingface", "local"]


def _get_provider_limits(config):
    """
    Read per-provider rate limits from config.json, resolving tier-based
    Gemini limits.

    Args:
        config (dict): Loaded config.json.

    Returns:
        dict: {provider_name: {"rpm": int, "rpd": int}}
    """
    provider_limits_cfg = config.get("provider_limits", {})
    gemini_tier = config.get("gemini_tier", "free")
    limits = {}

    for provider_name in _PROVIDER_NAMES:
        cfg = provider_limits_cfg.get(provider_name, {})

        if provider_name == "gemini":
            # ── Resolve Gemini tier ────────────────────────────────────────
            tier_cfg = cfg.get(gemini_tier, cfg.get("free", {}))
            limits[provider_name] = {
                "rpm": tier_cfg.get("rpm", 5),
                "rpd": tier_cfg.get("rpd", 1500),
            }
        else:
            limits[provider_name] = {
                "rpm": cfg.get("rpm", PROVIDER_MAX_CALLS_FREE),
                "rpd": cfg.get("rpd", PROVIDER_MAX_CALLS_FREE),
            }

    return limits


def calculate_state(normalized_hour, source_call_counts, source_limits,
                    provider_call_counts, provider_limits,
                    low_score_streak, error_streak,
                    source_names):
    """
    Build the dynamic state vector expected by the DRL agent.

    Structure (v3.0 — Provider-Aware):
        [0]           hour / 24.0
        [1 .. 14]     source usage ratios (calls/limit)
        [15]          low_score_streak / MAX
        [16]          error_streak / MAX
        [17 .. 20]    provider usage ratios (gemini, deepseek, hf, local)

    Args:
        normalized_hour (float): Current hour / 24.0.
        source_call_counts (dict): {source_name: calls_made}.
        source_limits (dict): {source_name: max_calls}.
        provider_call_counts (dict): {provider_name: calls_made_today}.
        provider_limits (dict): {provider_name: {rpm, rpd}}.
        low_score_streak (int): Consecutive low-score papers.
        error_streak (int): Consecutive API errors.
        source_names (list of str): Working source names.

    Returns:
        np.ndarray: Float array of shape (1 + N_sources + 2 + 4,).
    """
    # ── Source usage ratios ─────────────────────────────────────────────────
    source_ratios = []
    for name in source_names:
        limit = max(source_limits.get(name, MAX_CALLS_PER_SOURCE), 1)
        ratio = min(source_call_counts.get(name, 0) / limit, 1.0)
        source_ratios.append(ratio)

    # ── Streak normalization ────────────────────────────────────────────────
    low_norm = min(low_score_streak / LOW_SCORE_MAX, 1.0)
    error_norm = min(error_streak / LOW_SCORE_MAX, 1.0)

    # ── Provider usage ratios ──────────────────────────────────────────────
    provider_ratios = []
    for provider_name in _PROVIDER_NAMES:
        rpd = provider_limits.get(provider_name, {}).get("rpd", PROVIDER_MAX_CALLS_FREE)
        ratio = min(provider_call_counts.get(provider_name, 0) / max(rpd, 1), 1.0)
        provider_ratios.append(ratio)

    return np.array(
        [normalized_hour] + source_ratios + [low_norm, error_norm] + provider_ratios,
        dtype=np.float32
    )


def execute_live_fetch(action, action_map, config):
    """
    Execute EXACTLY ONE live API call based on the DRL agent's action.

    Args:
        action (int): Dense action index (0..N-1 = query source N).
        action_map (dict): {action: (source_name, SourceClass)}.
        config (dict): Project configuration.

    Returns:
        tuple: (papers_found, error_occurred, source_name)
    """
    if action not in action_map:
        print(f"  [WARN] Action {action} has no mapped source. Skipping.")
        return [], True, "unknown"

    source_name, SourceClass = action_map[action]
    error_occurred = False
    papers = []

    try:
        source = SourceClass(config)
        if not getattr(source, "enabled", True):
            print(f"  [WARN] {source_name} is disabled (no API key). Skipping.")
            return papers, True, source_name

        print(f"  [{source_name}] Fetching papers...")
        papers = source.fetch_new_papers()

        if papers:
            print(f"  [{source_name}] Found {len(papers)} papers.")
        else:
            print(f"  [{source_name}] No new papers found.")

    except requests.HTTPError as e:
        print(f"  [ERR] [{source_name}] API error: {e}")
        error_occurred = True
    except requests.ConnectionError as e:
        print(f"  [ERR] [{source_name}] Connection error: {e}")
        error_occurred = True
    except Exception as e:
        print(f"  [ERR] [{source_name}] Unexpected error: {e}")
        error_occurred = True

    return papers, error_occurred, source_name


def evaluate_paper(paper, ai_manager, provider_call_counts):
    """
    Evaluate a fetched paper using the AI Manager and return a score.

    Args:
        paper (dict): Standardized paper dictionary.
        ai_manager (AIManager): AI evaluation manager.
        provider_call_counts (dict): {provider: count} — incremented
            when a provider is used.

    Returns:
        float: Overall score (0-10), or 0.0 if evaluation failed.
    """
    content = f"Title: {paper.get('title', 'N/A')}\nAbstract: {paper.get('abstract', '')}"
    try:
        evaluation = ai_manager.evaluate_paper_json(content, model_type='flash')
        if evaluation:
            # v1.1 FIX (provider attribution): credit the provider that ACTUALLY
            # served the request (exposed by AIManager v3.7 as last_provider_used),
            # instead of always crediting "gemini". This keeps the provider-usage
            # portion of the DRL state vector correct when fallback occurs.
            used = getattr(ai_manager, "last_provider_used", None) or "gemini"
            provider_call_counts[used] = provider_call_counts.get(used, 0) + 1
            return float(evaluation.get('overall_score', 0))
    except Exception as e:
        print(f"    [WARN] AI evaluation failed: {e}")
    return 0.0


def calculate_reward(score):
    """
    Convert an AI evaluation score to a DRL reward.

    Args:
        score (float): Paper evaluation score (0-10).

    Returns:
        float: Reward value.
    """
    if score >= SCORE_THRESHOLD_HIGH:
        return REWARD_HIGH
    elif score >= SCORE_THRESHOLD_MEDIUM:
        return REWARD_MEDIUM
    else:
        return REWARD_LOW


def run_live_loop(agent, action_map, working_source_names, config,
                  ai_manager, verbose=False):
    """
    Run the main live DRL agent loop with real API calls.

    This is the core orchestration loop extracted from talos_live_agent.py.
    It handles the full cycle repeatedly until shutdown is requested.

    Args:
        agent (TalosDRLAgent): Trained DRL agent.
        action_map (dict): Dense {action: (name, class)} mapping.
        working_source_names (list of str): Working source names.
        config (dict): Project configuration.
        ai_manager (AIManager): AI evaluation manager.
        verbose (bool): Whether to print detailed step info.

    Returns:
        dict: Shutdown statistics.
    """
    num_working = len(working_source_names)
    sleep_action = num_working

    # ── Source limits from config ──────────────────────────────────────────
    source_limits = {}
    for name in working_source_names:
        limit_key = f"{name}_limit"
        source_limits[name] = config.get(limit_key, MAX_CALLS_PER_SOURCE)

    # ── Provider limits (tier-based) ───────────────────────────────────────
    provider_limits = _get_provider_limits(config)

    # ── Counters ───────────────────────────────────────────────────────────
    source_call_counts = {name: 0 for name in working_source_names}
    provider_call_counts = {p: 0 for p in _PROVIDER_NAMES}
    active_cooldowns = {}    # action -> remaining steps (v3.1 cooldown)
    low_score_streak = 0
    error_streak = 0
    total_papers_fetched = 0
    high_score_count = 0
    episode_reward = 0.0

    print("  [INIT] Live agent ready. Starting main loop.\n")
    print("-" * 65)

    # ══════════════════════════════════════════════════════════════════════════
    # MAIN LIVE LOOP
    # ══════════════════════════════════════════════════════════════════════════

    shutdown_requested = False

    while not shutdown_requested:
        try:
            # ── Step 1: Calculate current state ────────────────────────────
            now = datetime.now()
            normalized_hour = now.hour / 24.0

            state = calculate_state(
                normalized_hour,
                source_call_counts, source_limits,
                provider_call_counts, provider_limits,
                low_score_streak, error_streak,
                working_source_names,
            )

            # ── Step 2: Decrement cooldowns (v3.1 — anti-deadlock) ──────────
            for a in list(active_cooldowns.keys()):
                active_cooldowns[a] -= 1
                if active_cooldowns[a] <= 0:
                    del active_cooldowns[a]

            # ── Step 3: Agent selects action (ε=0.05 exploration) ───────────
            action = agent.act(state, eps=0.05)

            # ── Cooldown override: if action is locked, pick random free action ─
            if action in active_cooldowns and action != sleep_action:
                free = [a for a in range(num_working) if a not in active_cooldowns]
                if free:
                    import random as _random
                    old_action = action
                    action = _random.choice(free)
                    print(f"  [COOLDOWN] Action {old_action} ({working_source_names[old_action]}) "
                          f"locked ({active_cooldowns.get(old_action, '?')} steps left) "
                          f"-> overridden to {action} ({working_source_names[action]})")

            if verbose:
                count_str = " ".join(
                    f"{name[:4]}={source_call_counts[name]}/{source_limits[name]}"
                    for name in working_source_names[:6]
                )
                prov_str = " ".join(
                    f"{p[:3]}={provider_call_counts[p]}/{provider_limits[p].get('rpd','?')}"
                    for p in _PROVIDER_NAMES
                )
                if action == sleep_action:
                    action_label = "SLEEP"
                else:
                    action_label = working_source_names[action] if action < num_working else "?"
                cd_str = f" cd={len(active_cooldowns)}" if active_cooldowns else ""
                print(f"\n  [ACT] {action_label} ({action}) | "
                      f"State: {count_str} low={low_score_streak} err={error_streak}{cd_str}")
                print(f"    Providers: {prov_str}")

            # ── Step 3: SLEEP action ───────────────────────────────────────
            if action == sleep_action:
                ratios = [
                    source_call_counts.get(n, 0) / max(source_limits.get(n, 1), 1)
                    for n in working_source_names
                ]
                if ratios and max(ratios) > 0.8:
                    print(f"  [SLEEP] Limits >80% -> sleeping 1h at {now.strftime('%H:%M')}")
                else:
                    print(f"  [SLEEP] Sleeping 1h at {now.strftime('%H:%M')}")
                time.sleep(SLEEP_SECONDS)
                source_call_counts = {name: 0 for name in working_source_names}
                provider_call_counts = {p: 0 for p in _PROVIDER_NAMES}
                continue

            # ── Step 4: Validate action ────────────────────────────────────
            if action < 0 or action >= num_working:
                print(f"  [WARN] Invalid action {action} (max={num_working - 1}). Skipping.")
                time.sleep(THROTTLE_SECONDS)
                continue

            source_name = working_source_names[action]

            # ── Step 5: Check source limit ──────────────────────────────────
            limit = source_limits.get(source_name, MAX_CALLS_PER_SOURCE)
            if source_call_counts[source_name] >= limit:
                print(f"  [WARN] {source_name} at limit ({limit} calls). Sleeping 1h...")
                time.sleep(SLEEP_SECONDS)
                source_call_counts = {name: 0 for name in working_source_names}
                provider_call_counts = {p: 0 for p in _PROVIDER_NAMES}
                continue

            # ── Step 6: Execute ONE live API call ──────────────────────────
            papers, error_occurred, fetched_source = execute_live_fetch(
                action, action_map, config
            )

            # ── Step 7: Update counters ────────────────────────────────────
            source_call_counts[source_name] += 1

            if error_occurred:
                error_streak += 1
                low_score_streak = 0
                reward = REWARD_ERROR
                print(f"    [ERR] API Error | Reward: {reward:.0f} | Error streak: {error_streak}")
                episode_reward += reward
            elif not papers:
                low_score_streak += 1
                error_streak = 0
                reward = REWARD_LOW
                if verbose:
                    print(f"    [EMPTY] No papers found. Reward: {reward:.0f}")
                episode_reward += reward
            else:
                # ── Step 8: Evaluate papers via AI ─────────────────────────
                error_streak = 0
                best_score = 0.0

                for paper in papers:
                    score = evaluate_paper(paper, ai_manager, provider_call_counts)
                    if score > best_score:
                        best_score = score

                    if score >= SCORE_THRESHOLD_HIGH:
                        high_score_count += 1
                        print(f"    [HIGH] Score: {score:.1f} -- "
                              f"\"{paper.get('title', 'N/A')[:80]}\"")

                    total_papers_fetched += 1

                # ── Step 9: Calculate reward ──────────────────────────────
                reward = calculate_reward(best_score)

                if best_score < SCORE_THRESHOLD_MEDIUM:
                    low_score_streak += 1
                else:
                    low_score_streak = 0

                print(f"    [OK] [{source_name}] Best score: {best_score:.1f} | "
                      f"Reward: {reward:.0f} | Low streak: {low_score_streak}")
                episode_reward += reward

            # ── Step 10: Apply cooldown if reward < 0 (v3.1 anti-deadlock) ─
            if reward < 0 and action < num_working:
                active_cooldowns[action] = 5

            # ── Step 11: Throttle ───────────────────────────────────────────
            time.sleep(THROTTLE_SECONDS)

            # ── Periodic status report ─────────────────────────────────────
            if total_papers_fetched > 0 and total_papers_fetched % 10 == 0:
                print(f"\n  [STAT] {total_papers_fetched} papers fetched | "
                      f"{high_score_count} high-score | Reward: {episode_reward:.0f}")

        except KeyboardInterrupt:
            print("\n  [STOP] KeyboardInterrupt received. Shutting down...")
            shutdown_requested = True
        except Exception as e:
            print(f"\n  [ERR] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            print("  [WAIT] Retrying in 30 seconds...")
            time.sleep(30)
            continue

    # ══════════════════════════════════════════════════════════════════════════
    # Return shutdown stats
    # ══════════════════════════════════════════════════════════════════════════

    return {
        "total_papers_fetched": total_papers_fetched,
        "high_score_count": high_score_count,
        "episode_reward": episode_reward,
    }