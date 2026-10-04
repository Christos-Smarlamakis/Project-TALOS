# -*- coding: utf-8 -*-
"""
Module: architecture_ledger.py
Project: TALOS v5.25.0
Description:
    Living architectural decision ledger for the TALOS codebase documentation
    subsystem. Persists three artefacts to ``data/cache/documentation_ledger.json``:
    the set of modules already documented, an append-only "why" decision log
    capturing the rationale behind each architectural choice, and a global
    symbol table mapping every module to its classes and functions. This ledger
    is the single source of truth that the relay orchestrator consults to carry
    prior decisions forward into subsequent documentation steps.

    Key design decisions:
    - JSON persistence with atomic UTF-8 writes so the ledger survives process
      restarts and remains diff-friendly.
    - A re-entrant lock serializes writes for concurrent relay workers.
    - Zero coupling to the cognitive mesh or CLI: only the standard library.

Dependencies:
    - json, os, threading, datetime: persistence, locking, timestamps.
    - typing: type annotations.
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)

_DEFAULT_LEDGER_PATH = os.path.join(
    _P or os.path.abspath(os.path.dirname(__file__)),
    "data",
    "cache",
    "documentation_ledger.json",
)


class ArchitectureLedger:
    """Living architectural decision ledger with a global symbol table.

    Attributes:
        ledger_path (str): Absolute path to the JSON ledger file.
    """

    def __init__(self, ledger_path: Optional[str] = None) -> None:
        self.ledger_path = ledger_path or _DEFAULT_LEDGER_PATH
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # -- Persistence -----------------------------------------------------
    # ------------------------------------------------------------------

    def load(self) -> Dict[str, Any]:
        """Load the ledger, returning an empty structure when absent.

        Returns:
            dict: The current ledger state.
        """
        with self._lock:
            if not os.path.exists(self.ledger_path):
                return self._empty_state()
            try:
                with open(self.ledger_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except (ValueError, OSError):
                return self._empty_state()
        if not isinstance(data, dict):
            return self._empty_state()
        data.setdefault("version", "5.25.0")
        data.setdefault("documented_modules", [])
        data.setdefault("decisions", [])
        data.setdefault("symbol_table", {})
        return data

    def save(self, data: Dict[str, Any]) -> None:
        """Atomically persist the ledger state as UTF-8 JSON.

        Args:
            data (dict): The ledger state to write.
        """
        data.setdefault("version", "5.25.0")
        data.setdefault("generated_at", _iso_now())
        parent = os.path.dirname(os.path.abspath(self.ledger_path))
        with self._lock:
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
            tmp = self.ledger_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
            os.replace(tmp, self.ledger_path)

    @staticmethod
    def _empty_state() -> Dict[str, Any]:
        return {
            "version": "5.25.0",
            "generated_at": _iso_now(),
            "documented_modules": [],
            "decisions": [],
            "symbol_table": {},
        }

    # ------------------------------------------------------------------
    # -- Decision log -----------------------------------------------------
    # ------------------------------------------------------------------

    def record_decision(
        self, module: str, decision: str, rationale: str = ""
    ) -> None:
        """Append an architectural "why" decision to the ledger.

        Args:
            module (str): Module path the decision concerns.
            decision (str): Short statement of the decision.
            rationale (str): The reasoning behind the decision.
        """
        data = self.load()
        entry = {
            "module": module,
            "decision": decision,
            "rationale": rationale,
            "timestamp": _iso_now(),
        }
        data["decisions"].append(entry)
        self.save(data)

    def decisions(self) -> List[Dict[str, Any]]:
        """Return the full append-only decision log.

        Returns:
            list[dict]: Chronological decision entries.
        """
        return self.load().get("decisions", [])

    # ------------------------------------------------------------------
    # -- Module tracking & symbol table ----------------------------------
    # ------------------------------------------------------------------

    def mark_documented(self, module_path: str) -> None:
        """Mark a module as documented in the ledger.

        Args:
            module_path (str): Project-relative module path.
        """
        data = self.load()
        modules = set(data.get("documented_modules", []))
        modules.add(module_path)
        data["documented_modules"] = sorted(modules)
        self.save(data)

    def documented_modules(self) -> Set[str]:
        """Return the set of modules already documented.

        Returns:
            set[str]: Documented module paths.
        """
        return set(self.load().get("documented_modules", []))

    def register_symbols(
        self, module_path: str, classes: List[str], functions: List[str]
    ) -> None:
        """Register a module's class and function names in the symbol table.

        Args:
            module_path (str): Project-relative module path.
            classes (list[str]): Class names in the module.
            functions (list[str]): Module-level function names.
        """
        data = self.load()
        table = data.setdefault("symbol_table", {})
        table[module_path] = {
            "classes": sorted(set(classes)),
            "functions": sorted(set(functions)),
        }
        data["symbol_table"] = table
        self.save(data)

    def symbol_table(self) -> Dict[str, Any]:
        """Return the global symbol table.

        Returns:
            dict: Module path to its classes and functions.
        """
        return self.load().get("symbol_table", {})

    def get_undocumented(self, discovered_modules: List[str]) -> List[str]:
        """Return discovered modules that are not yet documented.

        Args:
            discovered_modules (list[str]): All discovered module paths.

        Returns:
            list[str]: Modules missing from the documented set.
        """
        documented = self.documented_modules()
        return [m for m in discovered_modules if m not in documented]


def _iso_now() -> str:
    """Return the current UTC wall-clock time as an ISO 8601 string.

    Returns:
        str: ISO 8601 timestamp with timezone offset.
    """
    return datetime.now(timezone.utc).astimezone().isoformat()

