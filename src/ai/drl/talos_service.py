# -*- coding: utf-8 -*-
"""
Module: talos_service.py (v2.0 — Profile-Aware, Dynamic N Sources)
Project: TALOS v5.2.0 — Phase 5
Description:
    24/7 autonomous research service. Runs continuously on weak hardware
    (Raspberry Pi, old laptop, etc.) using the trained DRL agent to
    decide which APIs to query. NOW profile-aware — reads the active
    profile and loads the corresponding trained model. Supports ALL
    available sources dynamically (not just the original 3).

    How it works:
    - Loads the trained DRL agent model (models/dddqn_trained.pth),
      profile-aware: checks _profiles/<name>/models/ first.
    - Detects the active profile and its source list from config.json.
    - Enters an infinite loop: observe state → agent picks action →
      execute (query API or sleep) → get reward → notify if score≥8.
    - Uses dynamic source-name mapping from the environment (not hardcoded).
    - Uses LOW OS priority to avoid competing with interactive apps.
    - Enforces a mandatory 5-second sleep between cycles + gc.collect()
      to keep RAM usage under 100 MB.
    - The sleep action index is read from env.SLEEP_ACTION (dynamic).
    - Wrapped in a massive try/except — the daemon NEVER crashes.

    Usage:
        python scripts/talos_service.py
        python scripts/talos_service.py --verbose   # show every action

    Key design decisions:
    - Uses OfflineTalosEnv from train_agent.py (real DB scores) so
      rewards reflect actual paper quality, not simulation.
    - The DRL agent runs in inference-only mode (no learning, no replay
      buffer accumulation) to keep RAM low.
    - Notifications are fire-and-forget — if Telegram/Discord fail,
      the daemon continues uninterrupted.
    - Weekly digest email is sent EXACTLY once per Friday.
    - Dynamic source names from env.info["source"] (not hardcoded {0: "ArXiv"...}).

    ⚠️  This service runs INDEFINITELY. Use Ctrl+C to stop.
"""
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import time
import gc
import signal
import numpy as np
import json
from datetime import datetime, timedelta

# ── Add project root to Python's import path ────────────────────────────────
# ── Attempt to set LOW process priority (platform-specific) ─────────────────
try:
    # Unix/Linux/macOS: os.nice(10) adds 10 to the nice value
    # (lower priority, higher nice value)
    os.nice(10)
except AttributeError:
    # Windows: use psutil to set priority class
    try:
        import psutil
        p = psutil.Process()
        # BELOW_NORMAL_PRIORITY_CLASS = 0x00004000 (Windows constant)
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        print("  Process priority: LOW (BELOW_NORMAL on Windows)")
    except (ImportError, AttributeError):
        # psutil not installed — continue with default priority
        print("  WARNING: psutil not installed. Cannot lower process priority.")
else:
    print("  Process priority: LOW (nice +10)")

# ── Graceful shutdown handler ───────────────────────────────────────────────
_shutdown_requested = False


def _handle_signal(signum, frame):
    """Set the shutdown flag when Ctrl+C or SIGTERM is received."""
    global _shutdown_requested
    _shutdown_requested = True
    print("\n  ⏸️  Shutdown requested. Finishing current cycle...")


# Register Ctrl+C (SIGINT) and SIGTERM handlers
signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)

# ── Imports after priority setup ────────────────────────────────────────────
from src.core.notifier import TalosNotifier
from src.ai.drl.drl_agent import TalosDRLAgent, DEVICE
# Use OfflineTalosEnv for real database scores
from src.ai.drl.train_agent import OfflineTalosEnv


def format_paper_alert(paper_title, score, source, action_taken):
    """
    Format a notification message for a high-scoring paper.

    Args:
        paper_title (str): The paper's title.
        score (float): Overall evaluation score.
        source (str): API source name (e.g., "arxiv").
        action_taken (int): DRL action index that found this paper.

    Returns:
        str: Formatted alert message.
    """
    # ── Use the source name directly (dynamic, not hardcoded) ────────────────
    source_display = source.replace('_', ' ').title() if source else "Unknown"

    return (
        f"🧠 <b>TALOS Discovery Alert</b>\n\n"
        f"<b>Score:</b> {score:.1f}/10\n"
        f"<b>Source:</b> {source_display}\n"
        f"<b>DRL Action:</b> {action_taken}\n"
        f"<b>Title:</b> {paper_title[:500]}\n\n"
        f"<i>— TALOS Autonomous Research Service v5.2.0</i>"
    )


def should_send_weekly_digest(last_sent_date):
    """
    Check if it's time to send the weekly digest email.

    Sends every Friday between 17:00 and 18:00. Returns True only
    once per Friday (prevents duplicate emails within the same day).

    Args:
        last_sent_date (datetime.date or None): Date the last digest was sent.

    Returns:
        bool: True if a digest should be sent now.
    """
    now = datetime.now()
    # ── Only on Fridays, between 17:00 and 18:00 ──────────────────────────
    if now.weekday() != 4:  # 4 = Friday
        return False
    if now.hour != 17:
        return False
    # ── Don't send more than once per day ─────────────────────────────────
    if last_sent_date and last_sent_date == now.date():
        return False
    return True


def get_database_stats_for_digest():
    """
    Collect basic database statistics for the weekly digest.

    Returns:
        dict: Basic stats (total papers, elite count, avg score).
    """
    # We use raw sqlite3 to keep the import light and avoid
    # re-creating a full DatabaseManager instance.
    import sqlite3
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, 'talos_research.db')
    # ── Profile-aware path resolution ────────────────────────────────────
    profile_active = os.path.join(project_root, '_profiles', 'active_profile.txt')
    if os.path.exists(profile_active):
        try:
            with open(profile_active, 'r') as f:
                profile_name = f.read().strip()
            profile_db = os.path.join(project_root, '_profiles', profile_name, 'talos_research.db')
            if os.path.exists(profile_db):
                db_path = profile_db
        except Exception:
            pass

    stats = {"total": 0, "elite": 0, "avg_score": 0.0}
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM papers WHERE overall_score IS NOT NULL AND overall_score > 0")
            stats["total"] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM papers WHERE overall_score >= 8")
            stats["elite"] = c.fetchone()[0]
            c.execute("SELECT AVG(overall_score) FROM papers WHERE overall_score IS NOT NULL AND overall_score > 0")
            avg = c.fetchone()[0]
            stats["avg_score"] = round(avg, 2) if avg else 0.0
    except sqlite3.Error as e:
        print(f"  ⚠️  Could not read DB stats: {e}")
    return stats


def _save_daily_report(today_discoveries=None):
    """
    Save a daily report of high-scoring discoveries to a JSON log file.

    Args:
        today_discoveries (list, optional): List of discovery dicts with
            title, score, source, action, and timestamp keys.
    """
    if not today_discoveries:
        return
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        logs_dir = os.path.join(project_root, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        report_path = os.path.join(logs_dir, f"daily_report_{datetime.now().strftime('%Y%m%d')}.json")
        with open(report_path, 'a', encoding='utf-8') as f:
            for entry in today_discoveries:
                f.write(json.dumps(entry) + '\n')
    except Exception as e:
        print(f"  ⚠️  Could not save daily report: {e}")


def generate_weekly_digest_html(stats, papers_found_this_week):
    """
    Generate an HTML email body for the weekly digest.

    Args:
        stats (dict): Database statistics.
        papers_found_this_week (int): How many papers the daemon discovered.

    Returns:
        str: HTML email body.
    """
    now = datetime.now()
    return f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;color:#333;line-height:1.6">
<h2>🧠 TALOS Weekly Digest</h2>
<p><strong>Week ending:</strong> {now.strftime('%Y-%m-%d')}</p>
<hr>
<h3>📊 Database Status</h3>
<table style="border-collapse:collapse;width:100%">
<tr><td style="padding:6px"><b>Total Papers:</b></td><td>{stats['total']:,}</td></tr>
<tr><td style="padding:6px"><b>Elite Papers (≥8):</b></td><td>{stats['elite']:,}</td></tr>
<tr><td style="padding:6px"><b>Average Score:</b></td><td>{stats['avg_score']:.2f}</td></tr>
</table>
<hr>
<h3>🤖 Daemon Activity</h3>
<p><b>Papers discovered this week:</b> {papers_found_this_week}</p>
<p><b>DRL Agent:</b> LSTM-DDDQN running on {DEVICE}</p>
<p><b>Priority:</b> LOW (background task)</p>
<hr>
<p style="color:#888;font-size:0.85em">
<i>This is an automated message from the TALOS Autonomous Daemon v5.2.0.<br>
Project: <a href="https://github.com/Christos-Smarlamakis/Project-TALOS">github.com/Christos-Smarlamakis/Project-TALOS</a></i></p>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DAEMON LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Run the TALOS autonomous research daemon (v5.2.0 — profile-aware).

    This function is designed to run INDEFINITELY (24/7). It:
    - Detects the active profile and loads profile-specific config.
    - Loads the trained DRL agent (profile-aware model path).
    - Creates the offline environment with real DB scores.
    - Enters an infinite loop: observe → act → step → notify.
    - Uses dynamic source names from the environment.
    - Sends weekly digest emails on Fridays at 17:00.
    - Can only be stopped via Ctrl+C (SIGINT) or SIGTERM.
    """
    global _shutdown_requested

    # ── Profile detection ───────────────────────────────────────────────────
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    active_profile = "default"
    profile_file = os.path.join(project_root, '_profiles', 'active_profile.txt')
    if os.path.exists(profile_file):
        try:
            with open(profile_file, 'r') as f:
                active_profile = f.read().strip()
        except Exception:
            pass

    print("=" * 65)
    print("  TALOS Autonomous Research Service — v5.2.0")
    print("  Profile-Aware Background Research Agent")
    print("=" * 65)
    print(f"  Profile: {active_profile}")
    print(f"  Device: {DEVICE}")
    print(f"  Priority: LOW (background)")
    print(f"  Notifications: Telegram + Discord (score ≥ 8)")
    print(f"  Weekly Digest: Email every Friday 17:00")
    print(f"  Press Ctrl+C to stop")
    print("=" * 65)
    print()

    # ── Interactive reporting mode selection ───────────────────────────────
    try:
        import questionary
        mode = questionary.select(
            "Select reporting mode:",
            choices=[
                "1. Silent — alerts only (Telegram/Discord for score ≥ 8)",
                "2. Normal — episode summary every 10 episodes",
                "3. Verbose — every action printed",
            ]
        ).ask()
        if mode is None:
            print("  Cancelled. Exiting.")
            return
        verbose = "3." in mode  # Verbose mode
        normal = "2." in mode   # Normal mode (episode summaries)
        silent = "1." in mode   # Silent mode (alerts only)
    except ImportError:
        # questionary not installed — fall back to --verbose flag
        verbose = "--verbose" in sys.argv
        normal = False
        silent = True  # Default to silent without questionary

    # ══════════════════════════════════════════════════════════════════════════
    # INITIALISATION
    # ══════════════════════════════════════════════════════════════════════════

    # ── Create environment first (to get dimensions) ────────────────────────
    print("  [INIT] Creating offline environment (real DB scores)...")
    env = OfflineTalosEnv()

    # ── Build dynamic mapping from the environment ──────────────────────────
    # action → source name (e.g., 0 → "arxiv", 3 → "dblp", N → "sleep")
    num_sources = env.num_sources
    sleep_action = env.SLEEP_ACTION
    print(f"  [INIT] Sources: {num_sources} ({', '.join(env.source_names[:5])}...)" if num_sources > 5
          else f"  [INIT] Sources: {num_sources} ({', '.join(env.source_names)})")
    print(f"  [INIT] Observation dim: {env.observation_space.shape[0]}")
    print(f"  [INIT] Action dim: {env.action_space.n} (sources + sleep)")

    print("  [INIT] Loading DRL agent...")
    agent = TalosDRLAgent(
        state_dim=env.observation_space.shape[0],
        action_dim=env.action_space.n
    )

    # ── Load the trained model if available (profile-aware path) ────────────
    # Check profile-specific model first, then global
    model_paths = [
        os.path.join(project_root, '_profiles', active_profile, 'models', 'dddqn_trained.pth'),
        os.path.join(os.path.dirname(__file__), '..', 'models', 'dddqn_trained.pth'),
    ]
    loaded = False
    for model_path in model_paths:
        if os.path.exists(model_path):
            try:
                agent.load(model_path)
                print(f"  [INIT] Loaded trained model: {os.path.relpath(model_path, project_root)}")
                loaded = True
                break
            except Exception as e:
                print(f"  [INIT] Could not load {os.path.relpath(model_path, project_root)}: {e}")
    if not loaded:
        print("  [INIT] No trained model found. Using untrained agent (random actions).")

    # ── Use epsilon=0.0 for pure exploitation ────────────────────────────
    # In the live service, we trust the trained policy completely.
    # Random exploration is disabled — the agent uses ONLY its learned strategy.
    epsilon = 0.0

    # ── Initialise the notifier ────────────────────────────────────────────
    notifier = TalosNotifier()

    # ── Tracking variables ─────────────────────────────────────────────────
    papers_discovered = 0
    high_score_count = 0
    last_digest_date = None

    # ── Reporting summary ────────────────────────────────────────────────
    mode_label = "VERBOSE (every action)" if verbose else ("NORMAL (episode summaries)" if not silent else "SILENT (alerts only)")
    print(f"\n  📊 Reporting: {mode_label}")
    print(f"  🔔 Alerts:    Telegram + Discord (score ≥ 8)")
    print(f"  📧 Digest:    Email every Friday 17:00")
    print(f"\n  [INIT] Daemon ready. Starting main loop.\n")
    print("─" * 65)

    # ══════════════════════════════════════════════════════════════════════════
    # MAIN LOOP — runs FOREVER (until Ctrl+C)
    # ══════════════════════════════════════════════════════════════════════════

    while not _shutdown_requested:
        try:
            # ── Reset environment at the start of each "day" ──────────────
            obs, info = env.reset()
            agent.reset_hidden_states()
            episode_reward = 0.0
            episode_papers = []
            today_discoveries = []

            # ── One "day" = 200 steps (the episode limit) ─────────────────
            for step in range(200):
                if _shutdown_requested:
                    break

                # ── Agent chooses an action ───────────────────────────────
                # The agent sees the current observation (hour, API usage ratios,
                # error streaks) and decides which API to query.
                action = agent.act(obs, epsilon)

                # ── Execute the action in the environment ──────────────────
                # This simulates querying an API and getting a real paper score
                # from the database.
                next_obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                score = info.get("score", 0)

                # ── SLEEP action (dynamic index) ──────────────────────────
                # The agent decided to rest. Sleep for 1 hour to conserve
                # API limits and system resources.
                if action == sleep_action:
                    if verbose:
                        print(f"  😴 Action=SLEEP → sleeping 1 hour at {datetime.now().strftime('%H:%M')}")
                    time.sleep(3600)
                    obs = next_obs
                    continue

                # ── Throttle: mandatory cooldown between API calls ─────────
                # This keeps CPU at ~0% and gives APIs time to breathe.
                time.sleep(5)

                # ── Memory management: force garbage collection ────────────
                # Prevents RAM from growing over time due to Python's
                # reference cycles.
                gc.collect()

                # ── Notification: high-score alert ─────────────────────────
                if score >= 8:
                    high_score_count += 1
                    # ── Use the dynamic source name from the environment ───
                    source_name = info.get("source", "unknown")
                    alert_msg = format_paper_alert(
                        f"Paper from {source_name}", score, source_name, action
                    )
                    # Track for daily report
                    today_discoveries.append({
                        "title": f"Paper from {source_name}",
                        "score": score, "source": source_name,
                        "action": source_name,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    if verbose:
                        print(f"  🚨 HIGH SCORE ({score}) from {source_name} — sending alerts!")
                    notifier.telegram_send(alert_msg)
                    notifier.discord_send(alert_msg)
                    papers_discovered += 1

                elif verbose:
                    source_name = info.get("source", "?")
                    print(f"  [{source_name}] score={score}  reward={reward:.0f}  "
                          f"step={step+1}/200")

                # ── Advance to the next observation ────────────────────────
                obs = next_obs

                if terminated or truncated:
                    break

            # Daily report after each episode
            _save_daily_report(today_discoveries)

            # ════════════════════════════════════════════════════════════════
            # WEEKLY DIGEST CHECK — after each episode
            # ════════════════════════════════════════════════════════════════

            if should_send_weekly_digest(last_digest_date):
                print(f"\n  📧 Sending weekly digest email...")
                stats = get_database_stats_for_digest()
                html_body = generate_weekly_digest_html(stats, papers_discovered)
                notifier.email_send(
                    f"TALOS Weekly Digest — {datetime.now().strftime('%Y-%m-%d')}",
                    html_body
                )
                last_digest_date = datetime.now().date()
                # Reset the weekly counter
                papers_discovered = 0

            # ── Episode summary ────────────────────────────────────────────
            if verbose:
                print(f"\n  📊 Episode complete | Reward: {episode_reward:.0f} | "
                      f"High-score alerts sent: {high_score_count}")

        except KeyboardInterrupt:
            # ── Graceful shutdown ──────────────────────────────────────────
            print("\n  ⏸️  KeyboardInterrupt received. Shutting down...")
            break
        except Exception as e:
            # ── THE MASSIVE TRY/EXCEPT — nothing crashes the daemon ────────
            print(f"\n  ❌ Unexpected error in main loop: {e}")
            import traceback
            traceback.print_exc()
            print("  ⏳ Waiting 30 seconds before retrying...")
            time.sleep(30)
            # Continue the loop — the daemon NEVER dies
            continue

    # ══════════════════════════════════════════════════════════════════════════
    # SHUTDOWN
    # ══════════════════════════════════════════════════════════════════════════

    print("\n" + "=" * 65)
    print("  TALOS Autonomous Daemon — Shutdown Complete")
    print(f"  Total high-score papers discovered: {high_score_count}")
    print(f"  Uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Bye bye! 👋")
    print("=" * 65)


if __name__ == "__main__":
    main()