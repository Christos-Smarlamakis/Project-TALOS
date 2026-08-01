# -*- coding: utf-8 -*-
"""
Module: talos_live_agent.py (v3.2 — Batch 2 TUI hardening)
Project: TALOS v5.3.6
Description:
    Thin entry point for the TALOS Live DRL Agent. All heavy logic is
    now in core/ modules:
    - core/live_agent_sources.py     -> source discovery & mapping
    - core/live_agent_orchestrator.py -> main loop, state, provider, cooldown
    - core/drl_agent.py              -> DRL policy network
    - core/ai_manager.py             -> AI evaluation
    - core/talos_env.py              -> environment (for training)

    v3.2 (Batch 2 TUI audit — presentation layer only):
    - argparse replaces ad-hoc sys.argv scanning (--verbose, --help).
    - Formatted startup summary table for configuration values.
    - Top-level KeyboardInterrupt guard: Ctrl+C during startup (config
      load, AIManager init, model load) exits cleanly with code 0 instead
      of dumping a traceback. (Ctrl+C inside the loop was already handled
      by run_live_loop.)

    Usage:
        python scripts/talos_live_agent.py
        python scripts/talos_live_agent.py --verbose
"""
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import json
import argparse

from dotenv import load_dotenv
load_dotenv()

from src.ai.drl.drl_agent import TalosDRLAgent, DEVICE
from src.core.ai_manager import AIManager
from src.ai.drl.talos_env import _load_source_list, _try_load_config
from src.ai.drl.live_agent_sources import build_source_map
from src.ai.drl.live_agent_orchestrator import run_live_loop
from datetime import datetime


def _parse_args():
    """Parse CLI arguments (v3.2 — replaces ad-hoc sys.argv scanning)."""
    parser = argparse.ArgumentParser(
        description="TALOS Live DRL Agent — real-time academic API orchestration.")
    parser.add_argument("--verbose", action="store_true",
                        help="Print detailed per-step state and provider info.")
    return parser.parse_args()


def main():
    """Load config, discover sources, load model, run live loop."""
    args = _parse_args()
    config = _try_load_config()
    if config is None:
        project_root = _P if _P else os.getcwd()
        config_path = os.path.join(project_root, 'config.json')
        if not os.path.exists(config_path):
            config_path = os.path.join(project_root, 'config.template.json')
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"FATAL: Error loading config.json: {e}")
            sys.exit(1)

    all_source_names = _load_source_list(config)
    action_map, working_source_names = build_source_map(all_source_names)
    num_working = len(working_source_names)
    num_configured = len(all_source_names)

    # ── Formatted startup summary (v3.2) ─────────────────────────────────
    print("=" * 65)
    print("  TALOS Live DRL Agent v5.3.6 -- Provider-Aware")
    print("  Real-Time API Orchestration with LSTM-DDDQN")
    print("=" * 65)
    summary = [
        ("Device", str(DEVICE)),
        ("Configured sources", str(num_configured)),
        ("Working sources", f"{num_working} ({', '.join(working_source_names)})"),
        ("Gemini tier", config.get('gemini_tier', 'free')),
        ("Actions", f"0..{num_working - 1} = sources, {num_working} = Sleep(1h)"),
        ("Mode", "epsilon=0.05 exploration + 5-step cooldown"),
        ("Verbose", "ON" if args.verbose else "OFF"),
        ("Stop", "Press Ctrl+C"),
    ]
    for key, val in summary:
        print(f"  {key:<20} : {val}")
    print("=" * 65)
    print()

    verbose = args.verbose

    for name in all_source_names:
        if name not in working_source_names:
            print(f"  [WARN] Source '{name}' skipped (import failed or missing deps).")

    if num_working == 0:
        print("\n  [FATAL] No working sources found. Cannot start live agent.")
        sys.exit(1)

    ai_manager = AIManager(config)

    print("  [INIT] Loading trained DRL agent...")
    state_dim = 1 + num_working + 2 + 4
    action_dim = num_working + 1
    agent = TalosDRLAgent(state_dim=state_dim, action_dim=action_dim)

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

    stats = run_live_loop(agent, action_map, working_source_names,
                          config, ai_manager, verbose=verbose)

    print("\n" + "=" * 65)
    print("  TALOS Live DRL Agent -- Shutdown Complete")
    print(f"  Total papers fetched: {stats['total_papers_fetched']}")
    print(f"  High-score discoveries: {stats['high_score_count']}")
    print(f"  Episode reward: {stats['episode_reward']:.0f}")
    print(f"  Uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Shutting down.")
    print("=" * 65)


if __name__ == "__main__":
    # Top-level guard (v3.2): Ctrl+C during startup exits cleanly with
    # code 0 — no traceback dumped to the user.
    try:
        main()
    except KeyboardInterrupt:
        print("\n  [STOP] Interrupted during startup. Exiting cleanly.")
        sys.exit(0)
