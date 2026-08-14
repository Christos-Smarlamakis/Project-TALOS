# -*- coding: utf-8 -*-
"""
Module: red_tester_routes.py
Project: TALOS v5.9.16
Description:
    FastAPI APIRouter exposing REST endpoints for the Autonomous Red Tester
    (RL-Driven Chaos Engineering). Provides two endpoints:

    - GET /api/v1/tester/status: Returns the current Q-table (Component Fragility
      estimates) from data/red_tester_q_table.json. Falls back to zero-initialized
      table if no test run has occurred yet.
    - GET /api/v1/tester/reports: Lists all available Markdown crash reports in
      data/reports/red_tester/, sorted by timestamp descending.

    This router is integrated into src/api/main_api.py via app.include_router().

    Key design decisions:
    - Read-only endpoints: the actual testing is triggered via talos.py CLI or
      run_talos.bat/sh, not via REST (long-running subprocesses are unsuitable
      for synchronous HTTP handlers).
    - File-system-based: Q-table and reports are read from disk, making these
      endpoints stateless and restart-safe.
    - Pydantic v2 models with extra="ignore" for forward compatibility.

Dependencies:
    - fastapi: APIRouter, HTTPException.
    - pydantic: Response model validation (v2).
    - json, os, datetime: File I/O and timestamp parsing.
"""
import json
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# -- Resolve project root (same pattern as all src/*.py modules) --
_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
while _PROJECT_ROOT and not os.path.exists(os.path.join(_PROJECT_ROOT, 'talos.py')):
    _PROJECT_ROOT = os.path.dirname(_PROJECT_ROOT)

if _PROJECT_ROOT:
    sys.path.insert(0, _PROJECT_ROOT)

# -- Constants --
Q_TABLE_PATH = os.path.join(_PROJECT_ROOT, "data", "red_tester_q_table.json")
REPORTS_DIR = os.path.join(_PROJECT_ROOT, "data", "reports", "red_tester")

# -- Target arms metadata: dynamically discovered from src/ at runtime --
def _discover_target_arms() -> List[Dict[str, object]]:
    """Discover all .py files under src/ directories for the status endpoint.

    Returns:
        List of dicts with 'index' and 'name' keys for every discovered arm.
    """
    target_dirs = [
        "src/analysis",
        "src/ingestion",
        "src/ai",
        "src/utils",
        "src/core",
        "src/api",
    ]
    arms = []
    idx = 0
    for target_dir in target_dirs:
        dir_path = os.path.join(_PROJECT_ROOT, target_dir)
        if not os.path.isdir(dir_path):
            continue
        for root, dirs, files in os.walk(dir_path):
            for file in sorted(files):
                if file.endswith(".py") and file != "__init__.py":
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, _PROJECT_ROOT).replace("\\", "/")
                    module_part = rel_path.replace("/", ".").replace(".py", "")
                    display_name = f"{rel_path} ({module_part})"
                    arms.append({"index": idx, "name": display_name})
                    idx += 1
    return arms


TARGET_ARMS = _discover_target_arms()

# -- Router definition --
router = APIRouter(prefix="/api/v1/tester", tags=["red_tester"])


# ---------------------------------------------------------------------------
# -- Pydantic Models --
# ---------------------------------------------------------------------------

class ArmStatus(BaseModel):
    """Q-value status for a single test arm (system component)."""
    model_config = {"extra": "ignore"}
    index: int = Field(..., description="Arm index (0-based)")
    name: str = Field(..., description="Human-readable component name")
    q_value: float = Field(..., description="Estimated Q-value (fragility). Higher = more fragile.")
    fragility: str = Field(..., description="Human-readable fragility classification")


class TesterStatus(BaseModel):
    """Full status response for the Autonomous Red Tester."""
    model_config = {"extra": "ignore"}
    q_table_path: str = Field(..., description="Absolute path to the Q-table JSON file")
    arms: List[ArmStatus] = Field(..., description="Per-component Q-value status")
    epsilon: float = Field(0.2, description="Exploration probability")
    alpha: float = Field(0.1, description="Constant step-size for Q-value updates")


class CrashReportEntry(BaseModel):
    """Metadata for a single crash report file."""
    model_config = {"extra": "ignore"}
    filename: str = Field(..., description="Report filename (e.g., CRASH_REPORT_20260801_103000.md)")
    path: str = Field(..., description="Absolute path to the report file")
    size_bytes: int = Field(..., description="File size in bytes")
    created_at: str = Field(..., description="ISO 8601 creation timestamp (from filesystem)")


class TesterReports(BaseModel):
    """List of available crash reports."""
    model_config = {"extra": "ignore"}
    reports_dir: str = Field(..., description="Absolute path to the reports directory")
    count: int = Field(..., description="Number of reports found")
    reports: List[CrashReportEntry] = Field(default_factory=list, description="Report metadata, newest first")


# ---------------------------------------------------------------------------
# -- Helper functions --
# ---------------------------------------------------------------------------

def _classify_fragility(q_value: float) -> str:
    """Classify a Q-value into a human-readable fragility label.

    Args:
        q_value: Estimated Q-value (higher = more fragile).

    Returns:
        One of: "HIGH_FRAGILITY", "MODERATE", "LOW", "STABLE".
    """
    if q_value >= 40:
        return "HIGH_FRAGILITY"
    elif q_value >= 10:
        return "MODERATE"
    elif q_value > 0:
        return "LOW"
    else:
        return "STABLE"


def _load_q_table() -> Dict[int, float]:
    """Load the Q-table JSON, falling back to zeros if unavailable.

    Returns:
        Dict mapping arm index (int) to Q-value (float).
    """
    if os.path.exists(Q_TABLE_PATH):
        try:
            with open(Q_TABLE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return {int(k): float(v) for k, v in raw.items()}
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
    # Fallback: zero-initialized table
    return {i: 0.0 for i in range(len(TARGET_ARMS))}


# ---------------------------------------------------------------------------
# -- Endpoints --
# ---------------------------------------------------------------------------

@router.get("/status", response_model=TesterStatus)
async def get_tester_status():
    """Return the current Q-table (Component Fragility estimates).

    Reads the persisted Q-table from data/red_tester_q_table.json. If no test
    run has been performed yet, returns a zero-initialized table.

    Returns:
        TesterStatus with per-arm Q-values and fragility classifications.
    """
    q_table = _load_q_table()

    arms = []
    for arm_meta in TARGET_ARMS:
        idx = arm_meta["index"]
        q_val = q_table.get(idx, 0.0)
        arms.append(ArmStatus(
            index=idx,
            name=arm_meta["name"],
            q_value=q_val,
            fragility=_classify_fragility(q_val),
        ))

    return TesterStatus(
        q_table_path=Q_TABLE_PATH,
        arms=arms,
        epsilon=0.2,
        alpha=0.1,
    )


@router.get("/reports", response_model=TesterReports)
async def get_tester_reports():
    """List all available Markdown crash reports.

    Scans data/reports/red_tester/ for *.md files and returns metadata
    sorted by filesystem modification time (newest first).

    Returns:
        TesterReports with report metadata list.
    """
    if not os.path.isdir(REPORTS_DIR):
        return TesterReports(
            reports_dir=REPORTS_DIR,
            count=0,
            reports=[],
        )

    report_entries = []
    try:
        for entry in sorted(
            os.scandir(REPORTS_DIR),
            key=lambda e: e.stat().st_mtime,
            reverse=True,
        ):
            if entry.is_file() and entry.name.endswith(".md"):
                stat = entry.stat()
                report_entries.append(CrashReportEntry(
                    filename=entry.name,
                    path=entry.path,
                    size_bytes=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                ))
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan reports directory: {e}")

    return TesterReports(
        reports_dir=REPORTS_DIR,
        count=len(report_entries),
        reports=report_entries,
    )