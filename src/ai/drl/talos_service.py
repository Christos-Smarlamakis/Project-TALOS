# -*- coding: utf-8 -*-
"""
Module: talos_service.py (v2.1 — Profile-Aware, Dynamic N Sources)
Project: TALOS v5.10.5 — Phase 5
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
    - A daily digest email is sent once per day at 17:00.
    - Dynamic source names from env.info["source"] (not hardcoded {0: "ArXiv"...}).

      This service runs INDEFINITELY. Use Ctrl+C to stop.
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
import subprocess
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
    print("\nShutdown requested. Finishing current cycle...")


# Register Ctrl+C (SIGINT) and SIGTERM handlers
signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)

# ── Imports after priority setup ────────────────────────────────────────────
from src.core.notifier import TalosNotifier
from src.ai.drl.drl_agent import TalosDRLAgent, DEVICE
# Use OfflineTalosEnv for real database scores
from src.ai.drl.train_agent import OfflineTalosEnv
from config.settings import TALOS_VERSION
from rich.console import Console
from rich.panel import Panel
from src.utils.logger import get_logger

# -- Rich console instance for the daemon TUI --
console = Console()

# -- Structured logger (canonical factory) --
logger = get_logger("talos_service")

# -- 3-hour live search interval (seconds) --
LIVE_SEARCH_INTERVAL_SECONDS = 3 * 3600

# -- Fast Edge CPU server (Fermion) subprocess handle for self-hosting --
_FERMION_PROCESS = None


def _spawn_fermion_cpu_server(strategy):
    """
    Start the Fast Edge CPU server (Fermion) in the background.

    The daemon self-hosts its local CPU inference dependency on port 11435
    when the global hardware strategy requires CPU compute. The subprocess
    is spawned with subprocess.Popen so it runs in the background without
    blocking the daemon's main loop. This removes the dependency on the
    external .bat launcher.

    Args:
        strategy (str): The active TALOS_HARDWARE_STRATEGY value.

    Returns:
        subprocess.Popen or None: The spawned process, or None when the
            strategy does not require CPU compute or spawning fails.
    """
    global _FERMION_PROCESS
    if strategy not in ("cpu_gpu_split", "cpu_only"):
        return None
    try:
        _FERMION_PROCESS = subprocess.Popen(
            [sys.executable, "-m", "fermion", "serve", "--port", "11435"]
        )
        console.print(
            f"  [INIT] Hardware Strategy: {strategy}. "
            f"Auto-started Fast Edge CPU server (Port 11435)."
        )
        return _FERMION_PROCESS
    except Exception as e:
        console.print(
            f"  [WARN] Could not auto-start Fast Edge CPU server: {e}"
        )
        return None


def _terminate_fermion_cpu_server():
    """
    Stop the background Fermion CPU server during graceful shutdown.

    Terminates the self-hosted Fast Edge CPU server so the daemon does not
    leave an orphaned zombie process holding port 11435.
    """
    global _FERMION_PROCESS
    if _FERMION_PROCESS is not None:
        try:
            _FERMION_PROCESS.terminate()
            console.print(
                "  [SHUTDOWN] Fast Edge CPU server (Port 11435) terminated."
            )
        except Exception as e:
            console.print(
                f"  [WARN] Could not terminate Fast Edge CPU server: {e}"
            )
        finally:
            _FERMION_PROCESS = None

def build_paper_alert(paper_data, source):
    """
    Build the paper metadata dict shared by all notification channels.

    Uses the full paper record sampled from the database (via
    info["paper_data"]) when available; otherwise falls back to a
    source-derived placeholder so notifications stay informative even
    when the environment only supplies a score.

    Args:
        paper_data (dict or None): Full paper metadata from the DRL
            environment (title, authors_str, doi, url, source).
        source (str): API source name (e.g., "arxiv").

    Returns:
        dict: Paper metadata with keys title, authors_str, doi, url, source.
    """
    source_display = source.replace('_', ' ').title() if source else "Unknown"
    paper_data = paper_data or {}
    title = paper_data.get("title") or f"Paper from {source_display}"
    return {
        "title": title,
        "authors_str": paper_data.get("authors_str") or paper_data.get("authors"),
        "doi": paper_data.get("doi"),
        "url": paper_data.get("url"),
        "source": paper_data.get("source") or source_display,
    }


def _is_fresh_paper(paper_meta):
    """
    Determine whether a sampled paper is a genuinely NEW discovery.

    The offline DRL agent re-samples OLD papers already stored in the
    database from previous days. Those papers must NOT trigger Discord or
    Telegram alerts or Rich panels. A paper is considered fresh when it was
    just added to the database (processed_at within the last 24 hours) or has
    never been evaluated before (last_evaluated_at is NULL).

    Args:
        paper_meta (dict): Paper metadata dict (title, authors_str, doi, url,
            source) built by build_paper_alert().

    Returns:
        bool: True if the paper is fresh and should alert; False otherwise.
    """
    doi = paper_meta.get("doi")
    url = paper_meta.get("url")
    if not doi and not url:
        # No stable identifier available -- cannot verify freshness, stay silent.
        return False
    try:
        import sqlite3 as _sqlite3
        from src.core.database_manager import get_active_profile_db_path
        db_path = get_active_profile_db_path()
        with _sqlite3.connect(db_path) as conn:
            conn.row_factory = _sqlite3.Row
            if doi:
                row = conn.cursor().execute(
                    "SELECT processed_at, last_evaluated_at FROM papers WHERE doi = ?",
                    (doi,)).fetchone()
            else:
                row = conn.cursor().execute(
                    "SELECT processed_at, last_evaluated_at FROM papers WHERE url = ?",
                    (url,)).fetchone()
        if row is None:
            # Not present in the database -- treat as not fresh.
            return False
        processed_at = row["processed_at"]
        last_evaluated_at = row["last_evaluated_at"]
        # -- Never evaluated before: treat as a brand-new discovery --
        if not last_evaluated_at:
            return True
        # -- Added within the last 24 hours (date granularity) --
        if processed_at:
            try:
                processed = datetime.strptime(str(processed_at)[:10], "%Y-%m-%d").date()
                if (datetime.now().date() - processed).days <= 1:
                    return True
            except ValueError:
                pass
        return False
    except Exception:
        # Any database hiccup must not crash the daemon; default to silent.
        return False


def should_send_daily_digest(last_sent_date):
    """
    Check if it is time to send the daily digest email.

    Sends once per day at 17:00. Returns True only once per day (prevents
    duplicate emails within the same day).

    Args:
        last_sent_date (datetime.date or None): Date the last digest was sent.

    Returns:
        bool: True if a digest should be sent now.
    """
    now = datetime.now()
    # -- Only at 17:00 --
    if now.hour != 17:
        return False
    # -- Don't send more than once per day --
    if last_sent_date and last_sent_date == now.date():
        return False
    return True


def send_daily_digest(notifier):
    """
    Query the database for elite papers added or updated in the last 24
    hours and email them as the daily digest.

    Args:
        notifier (TalosNotifier): Configured notification sender.

    Returns:
        list of dict: The elite papers included in the digest (possibly empty).
    """
    papers = []
    try:
        from src.core.database_manager import DatabaseManager
        db = DatabaseManager()
        papers = db.get_recent_elite_papers(hours=24, min_score=7.0)
    except Exception as e:
        console.print(f"Could not query papers for daily digest: {e}")
    notifier.email_daily_digest(papers)
    return papers


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
        print(f"    Could not save daily report: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DAEMON LOOP
# ═══════════════════════════════════════════════════════════════════════════════

# -- v5.10.3: LLM Router Sub-Agent (daemon provider-routing delegate) --
_DAEMON_ROUTER = None
_DAEMON_ROUTER_IMPORT_FAILED = False
_DAEMON_NOMINAL_PROMPT_LENGTH = 512


def _get_daemon_router():
    """Return a cached LLMRouterSubAgent instance, or None when unavailable.

    Returns:
        LLMRouterSubAgent | None: The provider-selection sub-agent.
    """
    global _DAEMON_ROUTER, _DAEMON_ROUTER_IMPORT_FAILED
    if _DAEMON_ROUTER is None and not _DAEMON_ROUTER_IMPORT_FAILED:
        try:
            from src.ai.drl.llm_router_subagent import LLMRouterSubAgent
            _DAEMON_ROUTER = LLMRouterSubAgent()
        except Exception:
            _DAEMON_ROUTER_IMPORT_FAILED = True
            _DAEMON_ROUTER = None
    return _DAEMON_ROUTER


def _log_router_decision(source_name, provider, prompt_length):
    """Append a [DAEMON/ROUTER] decision to data/logs/talos_system.log.

    Args:
        source_name (str): Name of the source that produced the paper.
        provider (str | None): The provider selected by the sub-agent.
        prompt_length (int): Estimated prompt token length.
    """
    try:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        logs_dir = os.path.join(project_root, 'data', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, 'talos_system.log')
        provider_str = provider if provider else "none"
        timestamp = datetime.now().isoformat()
        with open(log_path, 'a', encoding='utf-8') as handle:
            handle.write(
                f"[{timestamp}] [DAEMON/ROUTER] source={source_name} "
                f"task_type=foraging_evaluation prompt_length={prompt_length} "
                f"provider={provider_str}\n"
            )
    except Exception:
        pass


def route_daemon_evaluation(source_name, prompt_length=_DAEMON_NOMINAL_PROMPT_LENGTH):
    """Route a background paper evaluation through the LLMRouterSubAgent.

    Args:
        source_name (str): Name of the source that produced the paper.
        prompt_length (int): Estimated prompt token length.

    Returns:
        str | None: The selected provider, or None if the router is unavailable.
    """
    router = _get_daemon_router()
    chosen = None
    if router is not None:
        chosen = router.select_provider(
            prompt_length, task_type="foraging_evaluation")
    _log_router_decision(source_name, chosen, prompt_length)
    return chosen


def _load_daemon_target_sources():
    """Read the daemon target sources from config.json.

    Returns:
        list of str: The configured daemon_target_sources, or an empty list.
    """
    import json
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    config_path = os.path.join(project_root, 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        sources = cfg.get("daemon_target_sources")
        if isinstance(sources, list):
            return [str(s) for s in sources]
        return []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _run_live_search():
    """
    Execute the intelligent live foraging pass via the TALOS Live DRL Agent.

    Spawns src/ai/drl/talos_live_agent.py in a child process so the
    network-heavy foraging does not destabilize the daemon's memory or crash
    the main loop. The agent runs autonomously for a bounded number of
    episodes (--episodes 15) and streams its reasoning to the daemon's
    terminal (stdout and stderr are inherited, not captured). Blocking: the
    daemon pauses until the foraging pass finishes.

    Returns:
        bool: True if the live agent subprocess exited with code 0.
    """
    import subprocess
    live_agent_script = os.path.join(os.path.dirname(__file__), 'talos_live_agent.py')
    try:
        headless_env = os.environ.copy()
        headless_env["TALOS_HEADLESS"] = "1"
        # -- v5.10.6: inject daemon target sources from config.json --
        cmd = [sys.executable, os.path.abspath(live_agent_script),
               "--episodes", "15", "--verbose"]
        target_sources = _load_daemon_target_sources()
        if target_sources:
            cmd += ["--sources"] + target_sources
        result = subprocess.run(
            cmd, stdout=None, stderr=None, timeout=3600, env=headless_env)
        if result.returncode == 0:
            logger.info("Live DRL foraging agent completed successfully.")
            return True
        logger.warning("Live DRL foraging agent exited with code %s.", result.returncode)
        return False
    except Exception as e:
        logger.warning("Live DRL foraging agent failed: %s", e)
        return False


def _run_daemon_iteration(env, agent, notifier, sleep_action, verbose, epsilon,
                          last_live_search, last_digest_date,
                          papers_discovered, high_score_count):
    """
    Execute one full episode cycle of the daemon's main loop.

    Encapsulates a single iteration of the `while True` loop so the
    daemon's resilience can be exercised hermetically by the chaos tests.
    The body is identical to the original inline loop: trigger the live
    search when the interval elapses, reset the environment, run one
    200-step episode, save the daily report, and optionally send the daily
    digest email.

    Args:
        env: OfflineTalosEnv instance (or a test double) exposing reset()
            and step().
        agent: Trained DRL agent exposing act() and reset_hidden_states().
        notifier: TalosNotifier instance (or a test double) for alerts.
        sleep_action (int): Action index that maps to the sleep/cooldown.
        verbose (bool): Whether to print per-action diagnostics.
        epsilon (float): Exploration rate (0.0 for pure exploitation).
        last_live_search (float): Unix timestamp of the last live search.
        last_digest_date (date | None): Date of the last digest email.
        papers_discovered (int): Cumulative discovered-paper counter.
        high_score_count (int): Cumulative high-score alert counter.

    Returns:
        tuple: (last_live_search, last_digest_date, papers_discovered,
            high_score_count) -- the updated tracking state.

    Raises:
        Any exception raised by env.step(), agent.act(), or the notification
        layer propagates to the caller (the daemon's root try/except).
    """
    # -- Reset environment at the start of each "day" --
    # -- 3-hour live search trigger --
    if time.time() - last_live_search >= LIVE_SEARCH_INTERVAL_SECONDS:
        logger.info("[DAEMON] 3-hour interval reached. Triggering live academic search...")
        if _run_live_search():
            last_live_search = time.time()

    obs, info = env.reset()
    agent.reset_hidden_states()
    episode_reward = 0.0
    episode_papers = []
    today_discoveries = []

    # -- One "day" = 200 steps (the episode limit) --
    for step in range(200):
        if _shutdown_requested:
            break

        # -- Agent chooses an action --
        # The agent sees the current observation (hour, API usage ratios,
        # error streaks) and decides which API to query.
        action = agent.act(obs, epsilon)

        # -- Execute the action in the environment --
        # This simulates querying an API and getting a real paper score
        # from the database.
        next_obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        score = info.get("score", 0)

        # -- SLEEP action (dynamic index) --
        # The agent decided to rest. Sleep for 1 hour to conserve
        # API limits and system resources.
        if action == sleep_action:
            with console.status("[bold #4a9eff]Waiting for next research cycle...[/]"):
                time.sleep(3600)
            obs = next_obs
            continue

        # -- v5.10.3: route the paper evaluation through the LLM Router Sub-Agent --
        routed_source = info.get("source", "unknown")
        routed_provider = route_daemon_evaluation(
            routed_source, prompt_length=_DAEMON_NOMINAL_PROMPT_LENGTH)
        if verbose and routed_provider:
            print(f"  [DAEMON/ROUTER] {routed_source} -> provider={routed_provider}")

        # -- Throttle: mandatory cooldown between API calls --
        # This keeps CPU at ~0% and gives APIs time to breathe.
        time.sleep(5)

        # -- Memory management: force garbage collection --
        # Prevents RAM from growing over time due to Python's
        # reference cycles.
        gc.collect()

        # -- Notification: high-score alert --
        if score >= 8:
            high_score_count += 1
            # -- Use the dynamic source name from the environment --
            source_name = info.get("source", "unknown")
            paper_data = info.get("paper_data", {})
            paper_meta = build_paper_alert(paper_data, source_name)
            # Track for daily report
            today_discoveries.append({
                "title": paper_meta["title"],
                "score": score, "source": source_name,
                "action": source_name,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            # -- Mute dummy/simulated alerts (no real metadata) --
            is_real_paper = (
                bool(paper_meta.get("authors_str"))
                and not paper_meta.get("title", "").startswith("Paper from")
            )
            # -- Freshness filter: alert only on truly NEW discoveries --
            # The offline RL agent re-samples OLD papers from previous
            # days; those must remain visually silent.
            if is_real_paper and not _is_fresh_paper(paper_meta):
                is_real_paper = False
            if is_real_paper:
                # -- Rich console panel for the discovery --
                score_style = "[bold gold1]" if score >= 7.0 else "[bold #4a9eff]"
                panel_content = f"Title: {paper_meta['title']}\n"
                panel_content += f"Source: [magenta]{paper_meta['source']}[/magenta]"
                if routed_provider:
                    panel_content += f"\nRouter Decision: [cyan]{routed_provider}[/cyan]"
                panel_content += f"\nScore: {score_style}{score}/10[/]"
                console.print(Panel(
                    panel_content,
                    title="Paper Discovered",
                    border_style="gold1" if score >= 7.0 else "#4a9eff",
                ))
                notifier.telegram_send(paper_meta, score, action_taken=action)
                notifier.discord_send(paper_meta, score, action_taken=action)
            papers_discovered += 1

        elif verbose:
            source_name = info.get("source", "?")
            print(f"  [{source_name}] score={score}  reward={reward:.0f}  "
                  f"step={step+1}/200")

        # -- Advance to the next observation --
        obs = next_obs

        if terminated or truncated:
            break

    # Daily report after each episode
    _save_daily_report(today_discoveries)

    # -- DAILY DIGEST CHECK -- after each episode (17:00) --

    if should_send_daily_digest(last_digest_date):
        console.print("[bold #006699]Sending daily digest email...[/]")
        send_daily_digest(notifier)
        last_digest_date = datetime.now().date()

    # -- Episode summary --
    if verbose:
        console.print(f"Episode complete | Reward: {episode_reward:.0f} | High-score alerts sent: {high_score_count}")

    return last_live_search, last_digest_date, papers_discovered, high_score_count

def main():
    """
    Run the TALOS autonomous research daemon (v5.10.5 — profile-aware).

    This function is designed to run INDEFINITELY (24/7). It:
    - Detects the active profile and loads profile-specific config.
    - Loads the trained DRL agent (profile-aware model path).
    - Creates the offline environment with real DB scores.
    - Enters an infinite loop: observe → act → step → notify.
    - Uses dynamic source names from the environment.
    - Sends a daily digest email at 17:00.
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

    console.print(Panel(
        "Service Active / 24-7 Mode",
        title="TALOS Autonomous Research Daemon",
        border_style="#006699",
        width=72,
    ))
    console.print(
        f"  Version: [cyan]v{TALOS_VERSION}[/cyan]  |  Profile: [cyan]{active_profile}[/cyan]  |  Device: [cyan]{DEVICE}[/cyan]\n"
        f"  Notifications: Telegram + Discord (score >= 8)\n"
        f"  Daily Digest: Email at 17:00  |  Press Ctrl+C to stop\n"
    )

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
    # -- Self-host the Fast Edge CPU server (Fermion, port 11435) --
    # The daemon auto-starts its local CPU inference dependency in the
    # background when the global hardware strategy requires CPU compute.
    # This removes the dependency on external .bat launchers.
    _hardware_strategy = os.environ.get("TALOS_HARDWARE_STRATEGY", "cpu_gpu_split")
    _spawn_fermion_cpu_server(_hardware_strategy)
    # -- Resolve active-profile DB and ensure the schema exists --
    try:
        from src.core.database_manager import DatabaseManager, get_active_profile_db_path
        _db_path = get_active_profile_db_path()
        _db = DatabaseManager(db_path=_db_path)
        _db.create_table()
        print(f"  [INIT] Database ready: {_db_path}")
    except Exception as e:
        print(f"  [INIT] Database init skipped: {e}")

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
    last_live_search = 0  # Start at 0 so the live search fires immediately on startup

    # ── Reporting summary ────────────────────────────────────────────────
    mode_label = "VERBOSE (every action)" if verbose else ("NORMAL (episode summaries)" if not silent else "SILENT (alerts only)")
    console.print(f"[bold #006699]Reporting:[/] {mode_label}")
    console.print(f"  Alerts: Telegram + Discord (score >= 8)")
    console.print(f"  Digest: Email daily at 17:00")
    console.print("[bold green][INIT] Daemon ready. Starting main loop.[/]")

    # ══════════════════════════════════════════════════════════════════════════
    # MAIN LOOP — runs FOREVER (until Ctrl+C)
    # ══════════════════════════════════════════════════════════════════════════

    while not _shutdown_requested:
        try:
            (last_live_search, last_digest_date, papers_discovered,
             high_score_count) = _run_daemon_iteration(
                env, agent, notifier, sleep_action, verbose, epsilon,
                last_live_search, last_digest_date, papers_discovered,
                high_score_count)
        except KeyboardInterrupt:
            # -- Graceful shutdown --
            console.print("KeyboardInterrupt received. Shutting down...")
            break
        except Exception as e:
            # -- THE MASSIVE TRY/EXCEPT: nothing crashes the daemon --
            console.print(f"Unexpected error in main loop: {e}")
            import traceback
            traceback.print_exc()
            console.print("Waiting 30 seconds before retrying...")
            time.sleep(30)
            # Continue the loop: the daemon NEVER dies
            continue


    # ══════════════════════════════════════════════════════════════════════════
    # SHUTDOWN
    # ══════════════════════════════════════════════════════════════════════════

    _terminate_fermion_cpu_server()

    console.print("[bold #006699]TALOS Autonomous Daemon - Shutdown Complete[/]")
    console.print(f"  Total high-score papers discovered: {high_score_count}")
    console.print(f"  Uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()