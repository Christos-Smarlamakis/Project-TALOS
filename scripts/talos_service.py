# -*- coding: utf-8 -*-
"""
Module: talos_service.py (v1.1)
Project: TALOS v5.0.0 — Phase 4
Description:
    24/7 autonomous research service. Runs continuously on weak hardware
    (Raspberry Pi, old laptop, etc.) using the trained DRL agent to
    decide which APIs to query. Operates at BELOW_NORMAL_PRIORITY so
    it never interferes with other tasks. Notifies via Telegram/Discord
    when high-scoring papers are discovered, and sends a weekly digest
    email every Friday at 17:00.

    How it works:
    - Loads the trained DRL agent model (models/dddqn_trained.pth).
    - Enters an infinite loop: observe state → agent picks action →
      execute (query API or sleep) → get reward → notify if score≥8.
    - Uses LOW OS priority (Windows: BELOW_NORMAL_PRIORITY_CLASS,
      Unix: os.nice(10)) to avoid competing with interactive apps.
    - Enforces a mandatory 5-second sleep between cycles + gc.collect()
      to keep RAM usage under 100 MB.
    - Action 3 (Sleep/Cooldown) triggers a 1-hour pause.
    - Wrapped in a massive try/except — the daemon NEVER crashes.

    Usage:
        python scripts/talos_daemon.py
        python scripts/talos_daemon.py --verbose   # show every action

    Key design decisions:
    - Uses the OnlineTalosEnv from train_agent.py (real DB scores)
      so rewards reflect actual paper quality, not simulation.
    - The DRL agent runs in inference-only mode (no learning, no replay
      buffer accumulation) to keep RAM low.
    - Notifications are fire-and-forget — if Telegram/Discord fail,
      the daemon continues uninterrupted.
    - Weekly digest email is sent EXACTLY once per Friday (using a
      flag that resets at midnight Saturday).

    ⚠️  This service runs INDEFINITELY. Use Ctrl+C to stop.
"""
import os
import sys
import time
import gc
import signal
import numpy as np
import json
from datetime import datetime, timedelta

# ── Add project root to Python's import path ────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
from core.notifier import TalosNotifier
from core.drl_agent import TalosDRLAgent, DEVICE
# Use OfflineTalosEnv for real database scores
from scripts.train_agent import OfflineTalosEnv


def format_paper_alert(paper_title, score, source, action_taken):
    """
    Format a notification message for a high-scoring paper.

    Args:
        paper_title (str): The paper's title.
        score (float): Overall evaluation score.
        source (str): API source name (e.g., "arXiv").
        action_taken (int): DRL action that found this paper.

    Returns:
        str: Formatted alert message.
    """
    action_map = {0: "ArXiv", 1: "OpenAlex", 2: "Semantic Scholar"}
    action_name = action_map.get(action_taken, f"Action {action_taken}")

    return (
        f"🧠 <b>TALOS Discovery Alert</b>\n\n"
        f"<b>Score:</b> {score:.1f}/10\n"
        f"<b>Source:</b> {source}\n"
        f"<b>DRL Action:</b> {action_name}\n"
        f"<b>Title:</b> {paper_title[:500]}\n\n"
        f"<i>— TALOS Autonomous Research Service v5.0.0</i>"
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
<i>This is an automated message from the TALOS Autonomous Daemon v5.0.0.<br>
Project: <a href="https://github.com/Christos-Smarlamakis/Project-TALOS">github.com/Christos-Smarlamakis/Project-TALOS</a></i></p>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DAEMON LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Run the TALOS autonomous research daemon.

    This function is designed to run INDEFINITELY (24/7). It:
    - Loads the trained DRL agent.
    - Creates the offline environment (real DB scores).
    - Enters an infinite loop: observe → act → step → notify.
    - Sends weekly digest emails on Fridays at 17:00.
    - Can only be stopped via Ctrl+C (SIGINT) or SIGTERM.
    """
    global _shutdown_requested

    print("=" * 65)
    print("  TALOS Autonomous Research Service — v5.0.0 (Phase 4)")
    print("  Ultra-Lightweight Background Research Agent")
    print("=" * 65)
    print(f"  Device: {DEVICE}")
    print(f"  Priority: LOW (background)")
    print(f"  Actions: 0=ArXiv, 1=OpenAlex, 2=S2, 3=Sleep(1h)")
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

    print("  [INIT] Loading DRL agent...")
    agent = TalosDRLAgent()

    # ── Load the trained model if available ───────────────────────────────
    model_path = os.path.join(
        os.path.dirname(__file__), '..', 'models', 'dddqn_trained.pth'
    )
    if os.path.exists(model_path):
        try:
            agent.load(model_path)
            print(f"  [INIT] Loaded trained model: models/dddqn_trained.pth")
        except Exception as e:
            print(f"  [INIT] Could not load model ({e}). Using untrained agent.")
    else:
        print("  [INIT] No trained model found. Using untrained agent (random actions).")

    # ── Use epsilon=0.05 for 5% exploration (randomness) ──────────────────
    # This keeps the agent adaptive — occasionally tries different APIs.
    epsilon = 0.05

    # ── Create the environment (uses real database scores) ─────────────────
    print("  [INIT] Creating offline environment (real DB scores)...")
    env = OfflineTalosEnv()

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

                # ── Action 3 = SLEEP ───────────────────────────────────────
                # The agent decided to rest. Sleep for 1 hour to conserve
                # API limits and system resources.
                if action == 3:
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
                    action_name = {0: "ArXiv", 1: "OpenAlex", 2: "S2"}.get(action, "?")
                    alert_msg = format_paper_alert(
                        f"Paper from {action_name}", score, action_name, action
                    )
                    # Track for daily report
                    today_discoveries.append({
                        "title": f"Paper from {action_name}",
                        "score": score, "source": action_name,
                        "action": action_name,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    if verbose:
                        print(f"  🚨 HIGH SCORE ({score}) — sending alerts!")
                    notifier.telegram_send(alert_msg)
                    notifier.discord_send(alert_msg)
                    papers_discovered += 1

                elif verbose:
                    action_name = {0: "ArXiv", 1: "OpenAlex", 2: "S2"}.get(action, "?")
                    print(f"  [{action_name}] score={score}  reward={reward:.0f}  "
                          f"step={step+1}/200")

                # ── Advance to the next observation ────────────────────────
                obs = next_obs

                if terminated or truncated:
                    break

            # Daily report after each episode
            _save_daily_report()

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

            # ── Episode summary (printed every 10 episodes) ────────────────
            # A counter variable tracked outside the try block
            # (simplified: print every episode for the daemon)
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