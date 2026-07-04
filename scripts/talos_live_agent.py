# -*- coding: utf-8 -*-
"""
Module: talos_live_agent.py (v2.0 — Dynamic N-Source Live Agent)
Project: TALOS v5.2.0 — The Live Agent
Description:
    Live DRL inference engine that wires the trained LSTM-DDDQN agent
    to the real internet.  Instead of simulating scores from the database,
    this script calls real academic APIs based on the agent's decisions.
    NOW supports ALL available sources dynamically (not just the original 3).

    How it works:
    1. Auto-detects all configured sources from config.json.
    2. Creates a dynamic action→source mapping from the environment.
    3. Loads the trained model (models/dddqn_trained.pth), profile-aware.
    4. Enters an infinite loop:
       a. Calculate the dynamic state vector (N sources + 2 patterns).
       b. Agent selects action (0..N-1 = query source, N = sleep).
       c. Execute EXACTLY ONE live API call via the chosen source.
       d. Evaluate the fetched paper via AIManager (AI scoring).
       e. Calculate reward based on the AI score.
       f. Update state counters (API calls, error/low-score streaks).
       g. Throttle (sleep 5s) and repeat.
    5. The sleep action index is env.SLEEP_ACTION (dynamic).

    Key design decisions:
    - Epsilon=0.0 (pure exploitation) — the agent uses its trained policy.
    - Each loop iteration makes EXACTLY ONE API call.
    - 429 errors are caught gracefully — they increment the error streak.
    - Source classes are imported dynamically from `sources.*` modules.
    - Moved from hardcoded 3 sources to full dynamic N-source support.

    Usage:
        python scripts/talos_live_agent.py
        python scripts/talos_live_agent.py --verbose   # show every action
"""
import os
import sys
import json
import time
import signal
import requests
import numpy as np
from datetime import datetime

# ── Add project root to Python's import path ────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from core.drl_agent import TalosDRLAgent, DEVICE
from core.ai_manager import AIManager
from core.talos_env import _load_source_list, _try_load_config

# ── Configuration ───────────────────────────────────────────────────────────
MAX_CALLS_PER_SOURCE = 100      # Default API call limit per "day"
SCORE_THRESHOLD_HIGH = 8         # Score ≥ 8 → high reward
SCORE_THRESHOLD_MEDIUM = 7       # Score ≥ 7 → medium reward
REWARD_HIGH = 20                 # +20 for high-scoring papers
REWARD_MEDIUM = 5                # +5 for medium-scoring papers
REWARD_LOW = -10                 # -10 for low-scoring papers
REWARD_ERROR = -50               # -50 for API errors (429, etc.)
REWARD_SLEEP = 2                 # +2 for sleeping when API limits >80%
SLEEP_SECONDS = 3600             # 1 hour sleep for the sleep action
THROTTLE_SECONDS = 5             # Mandatory cooldown between API calls
LOW_SCORE_MAX = 20               # Max consecutive low scores before normalizing

# ── Graceful shutdown handler ───────────────────────────────────────────────
_shutdown_requested = False


def _handle_signal(signum, frame):
    """Set the shutdown flag when Ctrl+C or SIGTERM is received."""
    global _shutdown_requested
    _shutdown_requested = True
    print("\n  ⏸️  Shutdown requested. Finishing current cycle...")


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def _import_source_class(source_name):
    """
    Dynamically import a source class from `sources.<name>_source`.

    Converts a source name like "arxiv" → imports `sources.arxiv_source.ArxivSource`.
    Uses naming conventions: `<name>_source.py` → class `<Name>Source`.

    Args:
        source_name (str): Source key (e.g., "arxiv", "semantic_scholar").

    Returns:
        class or None: The source class, or None if import fails.
    """
    # ── Build module path and class name ────────────────────────────────────
    module_name = f"sources.{source_name}_source"
    # TitleCase: "semantic_scholar" → "SemanticScholar"
    class_parts = [part.capitalize() for part in source_name.split("_")]
    class_name = "".join(class_parts) + "Source"

    try:
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name, None)
    except (ImportError, AttributeError) as e:
        print(f"  ⚠️  Could not import {class_name} from {module_name}: {e}")
        return None


def _build_source_map(source_names):
    """
    Build a dynamic action→(name, class) mapping for all configured sources.

    Args:
        source_names (list of str): Ordered source names from config.

    Returns:
        dict: {action_index: (display_name, SourceClass)} for sources that
              could be imported. Sources that fail import are excluded.
    """
    action_map = {}
    for idx, name in enumerate(source_names):
        cls = _import_source_class(name)
        if cls is not None:
            action_map[idx] = (name, cls)
    return action_map


def calculate_state(normalized_hour, call_counts, source_limits,
                    low_score_streak, error_streak, source_names):
    """
    Build the dynamic state vector expected by the DRL agent.

    Structure: [hour/24, usage_ratio_0, ..., usage_ratio_N-1,
                low_score_streak/MAX, error_streak/MAX]

    Args:
        normalized_hour (float): Current hour / 24.0.
        call_counts (dict): {source_name: calls_made}.
        source_limits (dict): {source_name: max_calls}.
        low_score_streak (int): Consecutive low-score papers.
        error_streak (int): Consecutive API errors.
        source_names (list of str): Ordered source names.

    Returns:
        np.ndarray: Dynamic-length float array.
    """
    ratios = []
    for name in source_names:
        limit = max(source_limits.get(name, MAX_CALLS_PER_SOURCE), 1)
        ratio = min(call_counts.get(name, 0) / limit, 1.0)
        ratios.append(ratio)

    low_norm = min(low_score_streak / LOW_SCORE_MAX, 1.0)
    error_norm = min(error_streak / LOW_SCORE_MAX, 1.0)

    return np.array(
        [normalized_hour] + ratios + [low_norm, error_norm],
        dtype=np.float32
    )


def execute_live_fetch(action, action_map, config):
    """
    Execute EXACTLY ONE live API call based on the DRL agent's action.

    Args:
        action (int): Action index (0..N-1 = query source N).
        action_map (dict): {action: (source_name, SourceClass)}.
        config (dict): Project configuration.

    Returns:
        tuple: (papers_found, error_occurred, source_name)
            - papers_found (list): Standardized paper dicts.
            - error_occurred (bool): True if an error happened.
            - source_name (str): Name of the source queried.
    """
    if action not in action_map:
        source_name = "unknown"
        print(f"  ⚠️  Action {action} has no mapped source. Skipping.")
        return [], True, source_name

    source_name, SourceClass = action_map[action]
    error_occurred = False
    papers = []

    try:
        # ── Initialize the source agent ──────────────────────────────────
        source = SourceClass(config)
        if not getattr(source, "enabled", True):
            # Source disabled (missing API key) — treat as error for RL penalty
            print(f"  ⚠️  {source_name} is disabled (no API key). Skipping.")
            error_occurred = True
            return papers, error_occurred, source_name

        # ── Fetch papers ─────────────────────────────────────────────────
        print(f"  [{source_name}] Fetching papers...")
        papers = source.fetch_new_papers()

        if papers:
            print(f"  [{source_name}] Found {len(papers)} papers.")
        else:
            print(f"  [{source_name}] No new papers found.")

    except requests.HTTPError as e:
        # 429 Too Many Requests or 403 Forbidden
        print(f"  ⚠️  [{source_name}] API error: {e}")
        error_occurred = True
    except requests.ConnectionError as e:
        print(f"  ⚠️  [{source_name}] Connection error: {e}")
        error_occurred = True
    except Exception as e:
        print(f"  ⚠️  [{source_name}] Unexpected error: {e}")
        error_occurred = True

    return papers, error_occurred, source_name


def evaluate_paper(paper, ai_manager):
    """
    Evaluate a fetched paper using the AI Manager and return a score.

    Args:
        paper (dict): Standardized paper dictionary.
        ai_manager (AIManager): AI evaluation manager.

    Returns:
        float: Overall score (0-10), or 0.0 if evaluation failed.
    """
    content = f"Title: {paper.get('title', 'N/A')}\nAbstract: {paper.get('abstract', '')}"
    try:
        evaluation = ai_manager.evaluate_paper_json(content, model_type='flash')
        if evaluation:
            return float(evaluation.get('overall_score', 0))
    except Exception as e:
        print(f"    ⚠️  AI evaluation failed: {e}")
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


def main():
    """Run the live DRL agent loop with real API calls (dynamic N sources)."""
    global _shutdown_requested

    # ── Load configuration ────────────────────────────────────────────────
    config = _try_load_config()
    if config is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        config_path = os.path.join(project_root, 'config.json')
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"FATAL: Error loading config.json: {e}")
            sys.exit(1)

    # ── Auto-detect available sources ──────────────────────────────────────
    source_names = _load_source_list(config)
    action_map = _build_source_map(source_names)
    sleep_action = len(source_names)  # Sleep = last index
    num_sources = len(source_names)

    print("=" * 65)
    print("  TALOS Live DRL Agent — v5.2.0 (Dynamic N-Source)")
    print("  Real-Time API Orchestration with Trained LSTM-DDDQN")
    print("=" * 65)
    print(f"  Device: {DEVICE}")
    print(f"  Sources: {num_sources} ({', '.join(source_names[:5])}...)" if num_sources > 5
          else f"  Sources: {num_sources} ({', '.join(source_names)})")
    print(f"  Mapped sources: {len(action_map)}/{num_sources}")
    print(f"  Actions: 0..{num_sources-1} = sources, {sleep_action} = Sleep(1h)")
    print(f"  Mode: Pure exploitation (ε=0.0)")
    print(f"  Press Ctrl+C to stop")
    print("=" * 65)
    print()

    verbose = "--verbose" in sys.argv

    # ── Show which sources couldn't be loaded ─────────────────────────────
    for name in source_names:
        idx = source_names.index(name)
        if idx not in action_map:
            print(f"  ⚠️  Source '{name}' skipped (import failed or missing dependencies).")

    ai_manager = AIManager(config)

    # ── Load trained DRL agent ─────────────────────────────────────────────
    print("  [INIT] Loading trained DRL agent...")

    # Compute observation dim: 1 (hour) + N (ratios) + 2 (streaks)
    state_dim = 1 + num_sources + 2
    action_dim = num_sources + 1  # N sources + sleep
    agent = TalosDRLAgent(state_dim=state_dim, action_dim=action_dim)

    # Profile-aware model loading
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    active_profile = "default"
    profile_file = os.path.join(project_root, '_profiles', 'active_profile.txt')
    if os.path.exists(profile_file):
        try:
            with open(profile_file, 'r') as f:
                active_profile = f.read().strip()
        except Exception:
            pass

    model_paths = [
        os.path.join(project_root, '_profiles', active_profile, 'models', 'dddqn_trained.pth'),
        os.path.join(os.path.dirname(__file__), '..', 'models', 'dddqn_trained.pth'),
    ]
    loaded = False
    for model_path in model_paths:
        if os.path.exists(model_path):
            try:
                agent.load(model_path)
                size_kb = os.path.getsize(model_path) / 1024
                print(f"  [INIT] Loaded trained model: {os.path.relpath(model_path, project_root)} ({size_kb:.1f} KB)")
                loaded = True
                break
            except Exception as e:
                print(f"  [INIT] Could not load {os.path.relpath(model_path, project_root)}: {e}")
    if not loaded:
        print("  [INIT] No trained model found. Using untrained agent (random actions).")

    # ── Initialize state ───────────────────────────────────────────────────
    # Per-source limits from config or defaults
    source_limits = {}
    for name in source_names:
        limit_key = f"{name}_limit"
        source_limits[name] = config.get(limit_key, MAX_CALLS_PER_SOURCE)

    call_counts = {name: 0 for name in source_names}
    low_score_streak = 0
    error_streak = 0
    total_papers_fetched = 0
    high_score_count = 0
    episode_reward = 0.0

    print("  [INIT] Live agent ready. Starting main loop.\n")
    print("─" * 65)

    # ══════════════════════════════════════════════════════════════════════════
    # MAIN LIVE LOOP
    # ══════════════════════════════════════════════════════════════════════════

    while not _shutdown_requested:
        try:
            # ── Step 1: Calculate current state ────────────────────────────
            now = datetime.now()
            normalized_hour = now.hour / 24.0

            state = calculate_state(
                normalized_hour, call_counts, source_limits,
                low_score_streak, error_streak, source_names
            )

            # ── Step 2: Agent selects action (pure exploitation) ───────────
            action = agent.act(state, eps=0.0)

            if verbose:
                # Build dynamic display string for call counts
                count_str = " ".join(
                    f"{name[:4]}={call_counts[name]}/{source_limits[name]}"
                    for name in source_names[:6]
                )
                if action == sleep_action:
                    action_label = "SLEEP"
                else:
                    action_label = source_names[action] if action < num_sources else "?"
                print(f"\n  🎯 Action: {action_label} ({action}) | "
                      f"State: {count_str}"
                      f" low={low_score_streak} err={error_streak}")

            # ── Step 3: SLEEP action (dynamic index) ────────────────────────
            if action == sleep_action:
                # Check if most sources are near their limits
                ratios = [
                    call_counts.get(n, 0) / max(source_limits.get(n, 1), 1)
                    for n in source_names
                ]
                if ratios and max(ratios) > 0.8:
                    print(f"  😴 Action=SLEEP (limits >80%) → sleeping 1 hour at {now.strftime('%H:%M')}")
                else:
                    print(f"  😴 Action=SLEEP → sleeping 1 hour at {now.strftime('%H:%M')}")
                time.sleep(SLEEP_SECONDS)
                # Reset call counters after sleep (new "day")
                call_counts = {name: 0 for name in source_names}
                continue

            # ── Step 4: Validate action is within range ────────────────────
            if action < 0 or action >= num_sources:
                print(f"  ⚠️  Invalid action {action} (max={num_sources-1}). Skipping.")
                time.sleep(THROTTLE_SECONDS)
                continue

            source_name = source_names[action]

            # ── Step 5: Check if source is at its limit ────────────────────
            limit = source_limits.get(source_name, MAX_CALLS_PER_SOURCE)
            if call_counts[source_name] >= limit:
                print(f"  ⚠️  {source_name} at limit ({limit} calls). "
                      f"Sleeping 1 hour to reset...")
                time.sleep(SLEEP_SECONDS)
                call_counts = {name: 0 for name in source_names}
                continue

            # ── Step 6: Execute EXACTLY ONE live API call ──────────────────
            papers, error_occurred, fetched_source = execute_live_fetch(
                action, action_map, config
            )

            # ── Step 7: Update counters ────────────────────────────────────
            call_counts[source_name] += 1

            if error_occurred:
                # API error — heavy penalty
                error_streak += 1
                low_score_streak = 0
                reward = REWARD_ERROR
                print(f"    ❌ API Error! Reward: {reward:.0f} | "
                      f"Error streak: {error_streak}")
                episode_reward += reward
            elif not papers:
                # No papers found — neutral, treat as low score
                low_score_streak += 1
                error_streak = 0
                reward = REWARD_LOW
                if verbose:
                    print(f"    📭 No papers found. Reward: {reward:.0f}")
                episode_reward += reward
            else:
                # ── Step 8: Evaluate papers via AI ─────────────────────────
                error_streak = 0
                best_score = 0.0

                for paper in papers:
                    score = evaluate_paper(paper, ai_manager)
                    if score > best_score:
                        best_score = score

                    if score >= SCORE_THRESHOLD_HIGH:
                        high_score_count += 1
                        print(f"    🚨 HIGH SCORE: {score:.1f} — "
                              f"\"{paper.get('title', 'N/A')[:80]}\"")

                    total_papers_fetched += 1

                # ── Step 9: Calculate reward ──────────────────────────────
                reward = calculate_reward(best_score)

                if best_score < SCORE_THRESHOLD_MEDIUM:
                    low_score_streak += 1
                else:
                    low_score_streak = 0

                print(f"    ✅ [{source_name}] Best score: {best_score:.1f} | "
                      f"Reward: {reward:.0f} | Low streak: {low_score_streak}")
                episode_reward += reward

            # ── Step 10: Throttle between API calls ────────────────────────
            time.sleep(THROTTLE_SECONDS)

            # ── Periodic status report ─────────────────────────────────────
            if total_papers_fetched > 0 and total_papers_fetched % 10 == 0:
                print(f"\n  📊 Status: {total_papers_fetched} papers fetched | "
                      f"{high_score_count} high-score | "
                      f"Reward: {episode_reward:.0f}")

        except KeyboardInterrupt:
            print("\n  ⏸️  KeyboardInterrupt received. Shutting down...")
            break
        except Exception as e:
            print(f"\n  ❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            print("  ⏳ Waiting 30 seconds before retrying...")
            time.sleep(30)
            continue

    # ══════════════════════════════════════════════════════════════════════════
    # SHUTDOWN
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 65)
    print("  TALOS Live DRL Agent — Shutdown Complete")
    print(f"  Total papers fetched: {total_papers_fetched}")
    print(f"  High-score discoveries: {high_score_count}")
    print(f"  Episode reward: {episode_reward:.0f}")
    print(f"  Uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Bye bye! 👋")
    print("=" * 65)


if __name__ == "__main__":
    main()