# -*- coding: utf-8 -*-
"""
Module: system_diagnostics.py
Project: TALOS v5.16.1
Description:
    System Diagnostics Analyzer for TALOS. Executes an 8-point pre-flight
    health check over the local, air-gapped runtime (Python environment,
    SQLite database, local AI runtime, port availability, filesystem
    permissions, environment credentials, daemon status, and optional
    network endpoints) and renders a structured Rich health report with a
    one-line copy-paste remediation for every failure.

    The engine conforms to ISO/IEC 25010 Diagnosability and Fault Tolerance:
    every probe is isolated, non-fatal, and returns a structured result
    (PASS / WARN / FAIL) so a partial failure never aborts the full scan.
    Local components are always probed before optional network endpoints so
    the analyzer remains fully functional in a completely offline deployment.

Dependencies:
    - os, sys, sqlite3, socket, json, platform: Environment and resource probing.
    - urllib.request: HTTP probes (Ollama tags and network endpoints).
    - concurrent.futures: ThreadPoolExecutor for concurrent endpoint probing.
    - time: High-resolution latency measurement.
    - rich: Console, Table, and box for the rendered health report.
    - dotenv: Safe parsing of the .env configuration surface.
    - src.core.database_manager: Active-profile database resolution.
"""
import os
import sys
import json
import socket
import sqlite3
import platform
import time
import urllib.request
import urllib.error
import concurrent.futures

# -- Resolve project root (same bootstrap pattern as all src/*.py modules) --
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

from rich.console import Console
from rich.table import Table
from rich import box


# ----------------------------------------------------------------------
# -- Result state helpers --
# ----------------------------------------------------------------------

def _result(component, target, status, detail, remediation):
    """Build a single structured probe result.

    Args:
        component (str): High-level system area being probed.
        target (str): The specific metric or resource under test.
        status (str): One of "PASS", "WARN", or "FAIL".
        detail (str): Human-readable description of the observed state.
        remediation (str): One-line copy-paste corrective action.

    Returns:
        dict: Structured probe result consumed by render_report().
    """
    return {
        "component": component,
        "target": target,
        "status": status,
        "detail": detail,
        "remediation": remediation,
    }


def _status(ok):
    """Map a tri-state probe outcome to a canonical status label.

    Args:
        ok (bool or None): True for PASS, None for WARN, False for FAIL.

    Returns:
        str: Canonical status label.
    """
    if ok is True:
        return "PASS"
    if ok is None:
        return "WARN"
    return "FAIL"


# ----------------------------------------------------------------------
# -- Canonical zero-key open academic repositories (v5.14.2) --
# ----------------------------------------------------------------------

# User-Agent used for all outbound diagnostic HTTP probes.
USER_AGENT = "TALOS-Research-Diagnostics/5.16.1"

# Zero-key (open access) academic repository endpoints probed concurrently.
# Each entry is a GET endpoint returning a small JSON/XML payload when the
# repository is reachable. The query term ("drone") is a lightweight neutral
# probe term; the endpoints require no API key or authentication.
OPEN_ACADEMIC_ENDPOINTS = {
    "arXiv": "https://export.arxiv.org/api/query?search_query=all:drone&max_results=1",
    "OpenAlex": "https://api.openalex.org/works?search=drone&per_page=1",
    "Crossref": "https://api.crossref.org/works?query=drone&rows=1",
    "DBLP": "https://dblp.org/search/publ/api?q=drone&format=json&h=1",
    "PubMed (NCBI)": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=drone&retmode=json&retmax=1",
    "OSTI (DOE)": "https://www.osti.gov/api/v1/records?term=drone&rows=1",
    "PLOS": "https://api.plos.org/search?q=drone&rows=1",
    "NASA NTRS": "https://ntrs.nasa.gov/api/citations/search?q=drone&page.size=1",
    "HAL": "https://api.archives-ouvertes.fr/search/?q=drone&wt=json&rows=1",
}


# ----------------------------------------------------------------------
# -- System Diagnostics Engine --
# ----------------------------------------------------------------------

class SystemDiagnosticsEngine:
    """Executes and renders the 8-point TALOS diagnostic health scan.

    Attributes:
        console (rich.console.Console): Rich console for report rendering.
        project_root (str): Absolute path to the TALOS project root.

    Usage:
        engine = SystemDiagnosticsEngine()
        results = engine.run_diagnostics(verbose=False)
        engine.render_report(results)
    """

    def __init__(self):
        self.console = Console()
        self.project_root = _P

    # ------------------------------------------------------------------
    # -- Probe 1: Python environment --
    # ------------------------------------------------------------------
    def check_python_environment(self):
        """Verify Python 3.11.x and the active talosenv conda environment.

        Returns:
            dict: Structured probe result.
        """
        version = platform.python_version()
        is_py311 = sys.version_info[:2] == (3, 11)

        conda_env = os.getenv("CONDA_DEFAULT_ENV", "")
        prefix = sys.prefix or ""
        prefix_name = os.path.basename(prefix.rstrip(os.sep))
        in_talosenv = conda_env == "talosenv" or prefix_name == "talosenv"

        if is_py311 and in_talosenv:
            return _result(
                "Python Environment",
                "Python 3.11.x / talosenv",
                "PASS",
                f"Python {version} running inside the 'talosenv' conda environment.",
                "No action required.",
            )
        if not is_py311:
            return _result(
                "Python Environment",
                "Python 3.11.x",
                "WARN",
                f"Python {version} detected; the canonical target is Python 3.11.x.",
                "conda activate talosenv && conda install python=3.11",
            )
        return _result(
            "Python Environment",
            "talosenv conda environment",
            "WARN",
            f"Python {version} detected but the active environment is "
            f"'{conda_env or prefix_name}', not 'talosenv'.",
            "conda activate talosenv",
        )

    # ------------------------------------------------------------------
    # -- Probe 2: Database integrity --
    # ------------------------------------------------------------------
    def check_database_integrity(self):
        """Validate the active-profile SQLite database and WAL journal mode.

        Returns:
            dict: Structured probe result.
        """
        try:
            from src.core.database_manager import get_active_profile_db_path
            db_path = get_active_profile_db_path()
        except Exception as exc:
            return _result(
                "Database Integrity",
                "Active profile database",
                "FAIL",
                f"Could not resolve the active profile database: {exc}",
                "python src/utils/db_stats.py",
            )

        if not os.path.exists(db_path):
            return _result(
                "Database Integrity",
                db_path,
                "FAIL",
                "Active profile database file does not exist yet.",
                "python talos.py --wizard   (initialize a profile and database)",
            )

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            integrity = cursor.execute("PRAGMA integrity_check;").fetchone()
            journal_mode = cursor.execute("PRAGMA journal_mode;").fetchone()
            conn.close()
        except Exception as exc:
            return _result(
                "Database Integrity",
                db_path,
                "FAIL",
                f"Could not open the database: {exc}",
                "python src/utils/db_stats.py --optimize",
            )

        integrity_ok = bool(integrity) and str(integrity[0]).lower() == "ok"
        journal_ok = bool(journal_mode) and str(journal_mode[0]).lower() == "wal"

        if integrity_ok and journal_ok:
            return _result(
                "Database Integrity",
                "PRAGMA integrity_check / journal_mode",
                "PASS",
                "Database integrity OK and journal_mode is WAL.",
                "No action required.",
            )
        if not integrity_ok:
            return _result(
                "Database Integrity",
                "PRAGMA integrity_check",
                "FAIL",
                f"Integrity check returned: {integrity[0] if integrity else 'unknown'}",
                "python src/utils/db_stats.py --optimize   (runs integrity_check + VACUUM)",
            )
        return _result(
            "Database Integrity",
            "PRAGMA journal_mode",
            "WARN",
            f"journal_mode is '{journal_mode[0] if journal_mode else 'unknown'}', expected 'wal'.",
            "python src/utils/db_stats.py --optimize",
        )

    # ------------------------------------------------------------------
    # -- Probe 3: Local AI runtime --
    # ------------------------------------------------------------------
    def check_local_ai_runtime(self):
        """Probe the Ollama runtime and verify the configured GPU model.

        Returns:
            dict: Structured probe result.
        """
        try:
            from config.settings import LOCAL_GPU_MODEL
            model_name = LOCAL_GPU_MODEL
        except Exception:
            model_name = os.getenv("LOCAL_GPU_MODEL", "llama3.1:8b")

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        tags_url = base_url.rstrip("/") + "/api/tags"

        try:
            req = urllib.request.Request(tags_url, method="GET")
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            models = {m.get("name", "") for m in payload.get("models", [])}
        except Exception as exc:
            return _result(
                "Local AI Runtime",
                tags_url,
                "WARN",
                f"Ollama not reachable ({exc}).",
                "ollama serve   (or start the Ollama desktop application)",
            )

        if model_name in models:
            return _result(
                "Local AI Runtime",
                f"Ollama model '{model_name}'",
                "PASS",
                f"Configured model '{model_name}' is installed and served.",
                "No action required.",
            )
        return _result(
            "Local AI Runtime",
            f"Ollama model '{model_name}'",
            "WARN",
            f"Model '{model_name}' not found among installed models.",
            f"ollama pull {model_name}",
        )

    # ------------------------------------------------------------------
    # -- Probe 4: Port availability --
    # ------------------------------------------------------------------
    @staticmethod
    def _port_listening(port, host="127.0.0.1"):
        """Return True when a TCP port is accepting connections.

        Args:
            port (int): TCP port to probe.
            host (str): Host address to probe (default loopback).

        Returns:
            bool: True when the port is listening.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        try:
            result = sock.connect_ex((host, port))
            return result == 0
        except OSError:
            return False
        finally:
            sock.close()

    def check_port_availability(self):
        """Probe TALOS, Synapse, and local AI ports for conflicts.

        Returns:
            dict: Structured probe result mapping each port to its state.
        """
        # -- (port, expected_running, label) --
        ports = [
            (8001, False, "TALOS FastAPI"),
            (8000, True, "SYNAPSE Event Bus"),
            (11434, True, "Ollama (GPU/Universal Local AI Runtime)"),
        ]
        results = {}
        for port, expected_running, label in ports:
            listening = self._port_listening(port)
            if expected_running:
                if listening:
                    results[str(port)] = _result(
                        "Port Availability", f"{label} ({port})", "PASS",
                        f"Port {port} is listening as expected.",
                        "No action required.",
                    )
                else:
                    results[str(port)] = _result(
                        "Port Availability", f"{label} ({port})", "WARN",
                        f"Port {port} is not listening.",
                        f"Start the {label} service to bind port {port}.",
                    )
            else:
                if listening:
                    results[str(port)] = _result(
                        "Port Availability", f"{label} ({port})", "WARN",
                        f"Port {port} is already occupied.",
                        f"Free port {port} before starting {label}, or change TALOS_API_PORT.",
                    )
                else:
                    results[str(port)] = _result(
                        "Port Availability", f"{label} ({port})", "PASS",
                        f"Port {port} is available.",
                        "No action required.",
                    )
        return results

    # ------------------------------------------------------------------
    # -- Probe 5: Filesystem permissions --
    # ------------------------------------------------------------------
    def check_filesystem_permissions(self):
        """Test read and write access on the core writable directories.

        Returns:
            dict: Structured probe result.
        """
        dirs = ["data", "_profiles", "logs"]
        failures = []
        for rel in dirs:
            target = os.path.join(self.project_root, rel)
            try:
                os.makedirs(target, exist_ok=True)
                probe = os.path.join(target, ".talos_diag_probe")
                with open(probe, "w", encoding="utf-8") as fh:
                    fh.write("ok")
                with open(probe, "r", encoding="utf-8") as fh:
                    fh.read()
                os.remove(probe)
            except Exception as exc:
                failures.append(f"{rel} ({exc})")

        if not failures:
            return _result(
                "Filesystem Permissions",
                "data/ _profiles/ logs/",
                "PASS",
                "Read and write access verified on all writable directories.",
                "No action required.",
            )
        return _result(
            "Filesystem Permissions",
            "data/ _profiles/ logs/",
            "FAIL",
            "Write access failed for: " + "; ".join(failures),
            "chmod -R u+rwX data _profiles logs   (or fix the folder permissions)",
        )

    # ------------------------------------------------------------------
    # -- Probe 6: Environment credentials --
    # ------------------------------------------------------------------
    def check_environment_credentials(self):
        """Validate the .env structure without exposing live secret values.

        Returns:
            dict: Structured probe result.
        """
        try:
            from dotenv import dotenv_values
            env_path = os.path.join(self.project_root, ".env")
            if not os.path.exists(env_path):
                return _result(
                    "Environment Credentials",
                    ".env",
                    "WARN",
                    "No .env file found at the project root.",
                    "copy example.env .env   (then fill in the required keys)",
                )
            values = dotenv_values(env_path)
            populated = [k for k, v in values.items() if v and str(v).strip()]
            return _result(
                "Environment Credentials",
                ".env structure",
                "PASS",
                f".env parsed with {len(values)} keys ({len(populated)} populated). Secret values redacted.",
                "No action required.",
            )
        except Exception as exc:
            return _result(
                "Environment Credentials",
                ".env structure",
                "FAIL",
                f"Could not parse .env: {exc}",
                "Validate .env formatting (no quotes around values, KEY=VALUE per line).",
            )

    # ------------------------------------------------------------------
    # -- Probe 7: Daemon status --
    # ------------------------------------------------------------------
    def check_daemon_status(self):
        """Detect whether the autonomous research daemon is running.

        Returns:
            dict: Structured probe result.
        """
        daemon_marker = "talos_service.py"
        try:
            import psutil
            for proc in psutil.process_iter(attrs=["cmdline", "name"]):
                cmdline = " ".join(proc.info.get("cmdline") or [])
                if daemon_marker in cmdline:
                    return _result(
                        "Daemon Status",
                        "talos_service.py",
                        "PASS",
                        f"Daemon process detected (PID {proc.pid}).",
                        "No action required.",
                    )
        except ImportError:
            pass
        except Exception as exc:
            return _result(
                "Daemon Status",
                "talos_service.py",
                "WARN",
                f"Could not inspect running processes: {exc}",
                "python src/ai/drl/talos_service.py",
            )
        return _result(
            "Daemon Status",
            "talos_service.py",
            "WARN",
            "No running talos_service.py daemon process detected.",
            "python src/ai/drl/talos_service.py",
        )

    # ------------------------------------------------------------------
    # -- Probe 8: Network endpoints (optional, local-first, concurrent) --
    # ------------------------------------------------------------------
    @staticmethod
    def _probe_single_endpoint(name, url):
        """Probe a single academic endpoint and return a structured result.

        Sends a lightweight HTTP GET with a strict 1.5s timeout and a
        canonical User-Agent, measuring the response latency in milliseconds.

        Args:
            name (str): Human-readable repository name.
            url (str): Endpoint URL to probe.

        Returns:
            dict: Structured probe result with ``component``, ``target``,
                ``status``, ``latency_ms``, ``detail``, and ``remediation``.
        """
        start = time.perf_counter()
        try:
            req = urllib.request.Request(
                url, method="GET", headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                code = resp.status
            latency_ms = int((time.perf_counter() - start) * 1000)
            if 200 <= code < 400:
                return {
                    "component": "Academic Ingestion Endpoints",
                    "target": f"{name}  HTTP {code} OK ({latency_ms}ms)",
                    "status": "PASS",
                    "latency_ms": latency_ms,
                    "detail": f"{name} responded HTTP {code} in {latency_ms}ms.",
                    "remediation": "No action required.",
                }
            return {
                "component": "Academic Ingestion Endpoints",
                "target": f"{name}  HTTP {code} ({latency_ms}ms)",
                "status": "WARN",
                "latency_ms": latency_ms,
                "detail": f"{name} responded HTTP {code} in {latency_ms}ms.",
                "remediation": f"Verify {name} service status; HTTP {code} may indicate rate limiting or an outage.",
            }
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {
                "component": "Academic Ingestion Endpoints",
                "target": f"{name}  OFFLINE",
                "status": "WARN",
                "latency_ms": latency_ms,
                "detail": f"{name} unreachable ({exc}). Network probes are optional in air-gapped mode.",
                "remediation": "No action required offline; verify network to enable this source.",
            }

    def check_network_endpoints(self):
        """Probe all zero-key open academic repositories concurrently.

        Uses a ThreadPoolExecutor sized to the endpoint count so all seven
        repositories are probed in parallel, bounding the total wall-clock
        time of this probe to roughly a single request timeout (1.5s).

        Returns:
            dict: Structured probe results keyed by repository name, in
                canonical endpoint order.
        """
        results = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(OPEN_ACADEMIC_ENDPOINTS),
        ) as executor:
            future_map = {
                executor.submit(self._probe_single_endpoint, name, url): name
                for name, url in OPEN_ACADEMIC_ENDPOINTS.items()
            }
            for future in concurrent.futures.as_completed(future_map):
                name = future_map[future]
                results[name] = future.result()

        # -- Preserve canonical endpoint ordering regardless of completion. --
        return {name: results[name] for name in OPEN_ACADEMIC_ENDPOINTS}

    # ------------------------------------------------------------------
    # -- Orchestration --
    # ------------------------------------------------------------------
    def run_diagnostics(self, verbose=False):
        """Execute all eight diagnostic probes in local-first order.

        Args:
            verbose (bool): Reserved for future verbose logging (unused).

        Returns:
            dict: Ordered probe results keyed by component, with nested
                dicts for multi-result probes (ports and endpoints).
        """
        return {
            "python_environment": self.check_python_environment(),
            "database_integrity": self.check_database_integrity(),
            "local_ai_runtime": self.check_local_ai_runtime(),
            "port_availability": self.check_port_availability(),
            "filesystem_permissions": self.check_filesystem_permissions(),
            "environment_credentials": self.check_environment_credentials(),
            "daemon_status": self.check_daemon_status(),
            "network_endpoints": self.check_network_endpoints(),
        }

    @staticmethod
    def _flatten_results(results):
        """Flatten nested probe results into a single ordered row list.

        Args:
            results (dict): Output of run_diagnostics().

        Returns:
            list[dict]: Ordered flat list of probe result dicts.
        """
        rows = []
        # -- Multi-result probes carry nested dicts keyed by sub-target. --
        for value in results.values():
            if isinstance(value, dict) and "status" not in value:
                rows.extend(value.values())
            else:
                rows.append(value)
        return rows

    def render_report(self, results):
        """Render a structured Rich health report table.

        Args:
            results (dict): Output of run_diagnostics().

        Returns:
            rich.table.Table: The rendered table (also printed to console).
        """
        table = Table(
            title="TALOS System Diagnostic Health Report",
            box=box.ROUNDED,
            border_style="bright_cyan",
            show_lines=True,
            header_style="bold bright_cyan",
        )
        table.add_column("Component", style="bold cyan", no_wrap=True)
        table.add_column("Target / Metric", style="white", no_wrap=True)
        table.add_column("Status", style="bold", justify="center")
        table.add_column("Remediation Guidance", style="white")

        style_map = {
            "PASS": "[bold green]PASS[/bold green]",
            "WARN": "[bold yellow]WARN[/bold yellow]",
            "FAIL": "[bold red]FAIL[/bold red]",
        }

        for row in self._flatten_results(results):
            table.add_row(
                row.get("component", ""),
                row.get("target", ""),
                style_map.get(row.get("status", ""), row.get("status", "")),
                row.get("remediation", ""),
            )
        self.console.print(table)
        return table

    def run_and_render(self):
        """Run diagnostics and render the health report in one call.

        Returns:
            dict: The raw diagnostic results.
        """
        results = self.run_diagnostics()
        self.render_report(results)
        return results


# ----------------------------------------------------------------------
# -- Standalone entry point --
# ----------------------------------------------------------------------
if __name__ == "__main__":
    engine = SystemDiagnosticsEngine()
    engine.run_and_render()

