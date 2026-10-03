# -*- coding: utf-8 -*-
"""
Module: hud_renderer.py
Project: TALOS v5.22.0
Description:
    Persistent telemetry HUD renderer for the TALOS Scientific Terminal
    Dashboard. Builds a compact two-row Rich Panel summarising the active
    research profile, the paper corpus metrics (total, elite foundational,
    Kitchenham-appraised), the hardware footprint (GPU name and VRAM), the
    local Ollama runtime status on port 11434, the active AI execution
    strategy, and the scavenged model count. Every probe is best-effort and
    air-gapped: a failed lookup degrades to a neutral placeholder rather than
    raising, honouring the never-crash guarantee of Constitution II and III.

Dependencies:
    - os, subprocess, socket, json: environment lookup and local port/GPU probing.
    - pathlib.Path: cache file resolution for the scavenged model count.
    - rich.panel.Panel, rich.table.Table, rich.text.Text, rich.align.Align,
      rich.box: styled rendering primitives.
    - config.settings: canonical network/hardware strategy constants.
    - src.core.profile_manager (lazy): active profile name resolution.
    - src.core.database_manager (lazy): paper corpus statistics.
"""

import json
import os
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# -- Project root (canonical _P walk-up pattern shared across src/*.py) ---------
_P = Path(__file__).resolve().parents[3]


class HudRenderer:
    """Render the persistent telemetry HUD as a compact Rich Panel.

    The HUD is the always-visible header of the Scientific Terminal Dashboard.
    It synthesises four classes of telemetry -- profile, corpus, hardware, and
    routing -- into a single two-row panel so the operator can read the entire
    system state at a glance without vertical scrolling.

    Attributes:
        profile_name (str): Cached active profile identifier.
    """

    def __init__(self) -> None:
        """Initialise the renderer with no external side effects."""
        self.profile_name: str = "default"

    # ------------------------------------------------------------------
    # -- Public API ----------------------------------------------------
    # ------------------------------------------------------------------

    def build_hud(self) -> Panel:
        """Build and return the two-row telemetry HUD panel.

        Returns:
            Panel: A styled Rich Panel containing the profile/corpus row and
                the hardware/routing row.
        """
        profile = self._profile_name()
        metrics = self._paper_metrics()
        gpu = self._gpu_name()
        vram = self._vram_gb()
        ollama = self._ollama_status()
        strategy = self._strategy_label()
        scavenged = self._scavenged_count()

        # -- Row 1: profile and paper corpus metrics --
        row1 = Text(no_wrap=True)
        row1.append("Profile: ", style="dim white")
        row1.append(profile, style="bold bright_cyan")
        row1.append("  |  Papers: ", style="dim white")
        row1.append(str(metrics["total"]), style="bold white")
        row1.append("  Elite Foundational: ", style="dim white")
        row1.append(str(metrics["elite"]), style="bold bright_green")
        row1.append("  Kitchenham Appraised: ", style="dim white")
        row1.append(
            str(metrics["appraised"]) if metrics["appraised"] is not None else "-",
            style="bold bright_magenta",
        )

        # -- Row 2: hardware, Ollama, strategy, scavenged models --
        row2 = Text(no_wrap=True)
        row2.append("GPU: ", style="dim white")
        row2.append(gpu or "N/A", style="bold white")
        if vram:
            row2.append(f" ({vram:.0f} GB VRAM)", style="bold cyan")
        row2.append("  |  Ollama :11434: ", style="dim white")
        row2.append(
            "ONLINE" if ollama else "OFFLINE",
            style="bold green" if ollama else "bold red",
        )
        row2.append("  |  Strategy: ", style="dim white")
        row2.append(strategy, style="bold yellow")
        row2.append("  |  Scavenged Models: ", style="dim white")
        row2.append(
            str(scavenged) if scavenged is not None else "-",
            style="bold cyan",
        )

        table = Table(show_header=False, box=None, padding=(0, 1), expand=False)
        table.add_column(justify="left", no_wrap=True)
        table.add_row(row1)
        table.add_row(row2)

        return Panel(
            Align.center(table),
            title="[bold]TALOS Telemetry HUD[/bold]",
            border_style="#006699",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    # ------------------------------------------------------------------
    # -- Telemetry probes (all best-effort, air-gapped) ----------------
    # ------------------------------------------------------------------

    def _profile_name(self) -> str:
        """Return the active profile name, defaulting to 'default'.

        Returns:
            str: The active profile identifier.
        """
        try:
            from src.core.profile_manager import get_active_profile_name

            name = get_active_profile_name() or "default"
            self.profile_name = name
            return name
        except Exception:
            return self.profile_name

    def _paper_metrics(self) -> Dict[str, Any]:
        """Return the paper corpus metrics used by the HUD.

        Returns:
            dict: Keys ``total``, ``elite``, and ``appraised``. ``appraised``
                is ``None`` when the quality-score column is unavailable.
        """
        metrics: Dict[str, Any] = {"total": 0, "elite": 0, "appraised": None}
        try:
            from src.core.database_manager import DatabaseManager

            db = DatabaseManager()
            stats = db.get_database_statistics()
            metrics["total"] = stats.get("total_papers", 0)
            metrics["elite"] = stats.get("elite_papers", 0)
            try:
                with db._connect() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT COUNT(*) FROM papers WHERE quality_score IS NOT NULL"
                    )
                    metrics["appraised"] = cur.fetchone()[0]
            except Exception:
                metrics["appraised"] = None
        except Exception:
            pass
        return metrics

    def _gpu_name(self) -> Optional[str]:
        """Detect the primary NVIDIA GPU name via nvidia-smi.

        Returns:
            Optional[str]: The GPU product name, or ``None`` on failure.
        """
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0].strip()
        except Exception:
            pass
        return None

    def _vram_gb(self) -> Optional[float]:
        """Return total GPU VRAM in GB, or ``None`` when undetectable.

        Returns:
            Optional[float]: Total VRAM in GB.
        """
        try:
            from src.core.hardware import detect_vram_gb

            return detect_vram_gb()
        except Exception:
            return None

    def _ollama_status(self, host: str = "127.0.0.1", port: int = 11434) -> bool:
        """Probe the local Ollama runtime on the default port.

        Args:
            host (str): Target host. Defaults to localhost.
            port (int): Target port. Defaults to 11434.

        Returns:
            bool: True when the port answers a connection within the timeout.
        """
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            return False

    def _strategy_label(self) -> str:
        """Return the active AI execution strategy label.

        Returns:
            str: Uppercased ``network/hardware`` strategy pair.
        """
        try:
            from config.settings import (
                TALOS_HARDWARE_STRATEGY,
                TALOS_NETWORK_STRATEGY,
            )

            net = os.environ.get("TALOS_NETWORK_STRATEGY", TALOS_NETWORK_STRATEGY)
            hw = os.environ.get("TALOS_HARDWARE_STRATEGY", TALOS_HARDWARE_STRATEGY)
            return f"{str(net).upper()}/{str(hw).upper()}"
        except Exception:
            return "UNKNOWN"

    def _scavenged_count(self) -> Optional[int]:
        """Count cached scavenged models from the benchmark cache.

        Returns:
            Optional[int]: The number of cached models, or ``None``.
        """
        cache = _P / "data" / "cache" / "llm_benchmarks.json"
        try:
            if not cache.exists():
                return None
            data = json.loads(cache.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return len(data)
            if isinstance(data, dict):
                for key in ("models", "benchmarks", "entries"):
                    if isinstance(data.get(key), list):
                        return len(data[key])
                return len(data)
        except Exception:
            return None
        return None
