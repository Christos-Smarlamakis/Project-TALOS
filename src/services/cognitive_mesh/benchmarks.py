# -*- coding: utf-8 -*-
"""
Module: benchmarks.py
Project: TALOS v5.24.0
Description:
    Scientific model benchmark client. Maintains a local, air-gapped cache of
    SOTA inference-model benchmark metrics (MMLU-Pro, HumanEval, cost per 1M
    tokens, time-to-first-token, and throughput) and maps them onto the four
    canonical scientific workloads: Fast Screening, Rigorous Audit, Code Audit,
    and Vector Embeddings. It reconciles cloud recommendations against the
    local RTX 4070 (12 GB VRAM) budget by delegating to the hardware advisor,
    and renders a Rich discovery matrix consumed by ``python talos.py
    --discover-llms``.

    Key design decisions:
    - The benchmark store lives at ``data/cache/llm_benchmarks.json`` and is
      seeded from a curated static table so the client is fully functional
      offline (Constitution II); any live scrape is best-effort and guarded.
    - The hardware advisor is imported lazily inside the reconciliation method
      so this module's top-level import surface stays light.
    - Role keys mirror the hardware advisor's four-role taxonomy so that local
      and cloud recommendations can be joined without re-keying.

Dependencies:
    - os, json, time: cache persistence and timestamps.
    - rich (lazy): terminal table rendering for --discover-llms.
    - src.core.hardware_advisor (lazy): local VRAM-budget reconciliation.
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
PROJECT_ROOT = _P

DEFAULT_CACHE_PATH = os.path.join(PROJECT_ROOT, "data", "cache", "llm_benchmarks.json")

# -- Role titles for rendering (ISO/IEC 25010 scientific workload taxonomy) ---
ROLE_TITLES: Dict[str, str] = {
    "fast_screening": "Fast Screening",
    "rigorous_audit": "Rigorous Audit (Kitchenham)",
    "code_audit": "Code Audit",
    "vector_embeddings": "Vector Embeddings",
}


# -- Curated static benchmark table (air-gapped seed) -------------------------
# Each record carries the scientific roles it can serve and its benchmark
# figures. This table is the offline source of truth; a live scrape may merge
# additional records but can never remove these seeds.
DEFAULT_BENCHMARKS: List[Dict[str, Any]] = [
    {
        "model": "llama-3.3-70b-versatile", "provider": "groq",
        "roles": ["fast_screening"], "mmlu_pro": 66.0, "human_eval": 85.0,
        "cost_per_1m_usd": 1.38, "ttft_ms": 180, "throughput_tps": 320,
    },
    {
        "model": "Meta-Llama-3.1-405B-Instruct", "provider": "sambanova",
        "roles": ["fast_screening", "rigorous_audit"], "mmlu_pro": 80.0,
        "human_eval": 82.0, "cost_per_1m_usd": 3.00, "ttft_ms": 120,
        "throughput_tps": 250,
    },
    {
        "model": "deepseek-r1", "provider": "deepseek",
        "roles": ["rigorous_audit", "code_audit"], "mmlu_pro": 84.0,
        "human_eval": 90.0, "cost_per_1m_usd": 1.37, "ttft_ms": 600,
        "throughput_tps": 80,
    },
    {
        "model": "claude-sonnet-4-5", "provider": "anthropic",
        "roles": ["rigorous_audit"], "mmlu_pro": 88.0, "human_eval": 93.0,
        "cost_per_1m_usd": 18.00, "ttft_ms": 700, "throughput_tps": 60,
    },
    {
        "model": "qwen2.5-coder:14b", "provider": "ollama",
        "roles": ["code_audit"], "mmlu_pro": 62.0, "human_eval": 78.0,
        "cost_per_1m_usd": 0.0, "ttft_ms": 400, "throughput_tps": 40,
    },
    {
        "model": "qwen2.5:14b", "provider": "ollama",
        "roles": ["rigorous_audit", "fast_screening"], "mmlu_pro": 70.5,
        "human_eval": 70.0, "cost_per_1m_usd": 0.0, "ttft_ms": 350,
        "throughput_tps": 45,
    },
    {
        "model": "llama3.1:8b", "provider": "ollama",
        "roles": ["fast_screening"], "mmlu_pro": 60.0, "human_eval": 60.0,
        "cost_per_1m_usd": 0.0, "ttft_ms": 200, "throughput_tps": 60,
    },
    {
        "model": "nomic-embed-text", "provider": "ollama",
        "roles": ["vector_embeddings"], "mmlu_pro": 0.0, "human_eval": 0.0,
        "cost_per_1m_usd": 0.0, "ttft_ms": 15, "throughput_tps": 900,
    },
    {
        "model": "text-embedding-3-small", "provider": "gemini",
        "roles": ["vector_embeddings"], "mmlu_pro": 0.0, "human_eval": 0.0,
        "cost_per_1m_usd": 0.02, "ttft_ms": 90, "throughput_tps": 500,
    },
]


# -- Fuzzy benchmark cross-reference table (v5.21.1) ---------------------------
# Each pattern is matched case-insensitively (in priority order) against a model
# identifier. More specific patterns must precede generic family patterns so that
# a known derivative resolves to its exact figures before falling back to the
# base-family tier estimate.
FUZZY_BENCHMARK_PATTERNS: List[Dict[str, Any]] = [
    {"pattern": "claude-3-opus", "mmlu_pro": 90.0, "human_eval": 89.0, "ttft_ms": 800},
    {"pattern": "claude-3-5-sonnet", "mmlu_pro": 88.0, "human_eval": 93.0, "ttft_ms": 700},
    {"pattern": "claude-sonnet", "mmlu_pro": 88.0, "human_eval": 93.0, "ttft_ms": 700},
    {"pattern": "claude-3-5-haiku", "mmlu_pro": 70.0, "human_eval": 83.0, "ttft_ms": 300},
    {"pattern": "claude", "mmlu_pro": 84.0, "human_eval": 90.0, "ttft_ms": 650},
    {"pattern": "deepseek-r1", "mmlu_pro": 84.0, "human_eval": 90.0, "ttft_ms": 600},
    {"pattern": "deepseek-v3", "mmlu_pro": 82.0, "human_eval": 86.0, "ttft_ms": 400},
    {"pattern": "deepseek-reasoner", "mmlu_pro": 84.0, "human_eval": 90.0, "ttft_ms": 600},
    {"pattern": "deepseek-coder", "mmlu_pro": 62.0, "human_eval": 84.0, "ttft_ms": 400},
    {"pattern": "deepseek", "mmlu_pro": 80.0, "human_eval": 84.0, "ttft_ms": 500},
    {"pattern": "gpt-4o", "mmlu_pro": 89.0, "human_eval": 92.0, "ttft_ms": 500},
    {"pattern": "gpt-4", "mmlu_pro": 89.0, "human_eval": 91.0, "ttft_ms": 500},
    {"pattern": "gpt-5", "mmlu_pro": 91.0, "human_eval": 93.0, "ttft_ms": 500},
    {"pattern": "gpt-6", "mmlu_pro": 92.0, "human_eval": 94.0, "ttft_ms": 500},
    {"pattern": "o1", "token": True, "mmlu_pro": 90.0, "human_eval": 92.0, "ttft_ms": 900},
    {"pattern": "o3", "token": True, "mmlu_pro": 93.0, "human_eval": 95.0, "ttft_ms": 900},
    {"pattern": "qwen2.5-coder", "mmlu_pro": 62.0, "human_eval": 84.0, "ttft_ms": 400},
    {"pattern": "qwen2.5:72b", "mmlu_pro": 78.0, "human_eval": 74.0, "ttft_ms": 350},
    {"pattern": "qwen2.5:32b", "mmlu_pro": 74.0, "human_eval": 72.0, "ttft_ms": 350},
    {"pattern": "qwen2.5:14b", "mmlu_pro": 70.5, "human_eval": 70.0, "ttft_ms": 350},
    {"pattern": "qwen2.5:7b", "mmlu_pro": 66.0, "human_eval": 65.0, "ttft_ms": 200},
    {"pattern": "qwen2.5:3b", "mmlu_pro": 60.0, "human_eval": 58.0, "ttft_ms": 150},
    {"pattern": "qwen", "mmlu_pro": 70.0, "human_eval": 70.0, "ttft_ms": 300},
    {"pattern": "llama-3.1-405b", "mmlu_pro": 80.0, "human_eval": 82.0, "ttft_ms": 120},
    {"pattern": "llama3.1:405b", "mmlu_pro": 80.0, "human_eval": 82.0, "ttft_ms": 120},
    {"pattern": "llama-3.1-70b", "mmlu_pro": 74.0, "human_eval": 72.0, "ttft_ms": 250},
    {"pattern": "llama3.1:70b", "mmlu_pro": 74.0, "human_eval": 72.0, "ttft_ms": 250},
    {"pattern": "llama-3.1-8b", "mmlu_pro": 60.0, "human_eval": 60.0, "ttft_ms": 200},
    {"pattern": "llama3.1:8b", "mmlu_pro": 60.0, "human_eval": 60.0, "ttft_ms": 200},
    {"pattern": "llama-3.3-70b", "mmlu_pro": 74.0, "human_eval": 72.0, "ttft_ms": 180},
    {"pattern": "llama-4", "mmlu_pro": 85.0, "human_eval": 84.0, "ttft_ms": 150},
    {"pattern": "llama", "mmlu_pro": 70.0, "human_eval": 70.0, "ttft_ms": 250},
    {"pattern": "mistral-large", "mmlu_pro": 76.0, "human_eval": 70.0, "ttft_ms": 300},
    {"pattern": "mistral-nemo", "mmlu_pro": 68.0, "human_eval": 65.0, "ttft_ms": 200},
    {"pattern": "mistral", "mmlu_pro": 68.0, "human_eval": 65.0, "ttft_ms": 250},
    {"pattern": "gemma-3", "mmlu_pro": 68.0, "human_eval": 65.0, "ttft_ms": 250},
    {"pattern": "gemma3", "mmlu_pro": 68.0, "human_eval": 65.0, "ttft_ms": 250},
    {"pattern": "gemma-2", "mmlu_pro": 66.0, "human_eval": 62.0, "ttft_ms": 250},
    {"pattern": "gemma2", "mmlu_pro": 66.0, "human_eval": 62.0, "ttft_ms": 250},
    {"pattern": "gemma", "mmlu_pro": 66.0, "human_eval": 62.0, "ttft_ms": 250},
    {"pattern": "phi-4", "mmlu_pro": 60.0, "human_eval": 70.0, "ttft_ms": 250},
    {"pattern": "phi4", "mmlu_pro": 60.0, "human_eval": 70.0, "ttft_ms": 250},
    {"pattern": "nomic-embed", "mmlu_pro": 0.0, "human_eval": 0.0, "ttft_ms": 15},
    {"pattern": "text-embedding", "mmlu_pro": 0.0, "human_eval": 0.0, "ttft_ms": 90},
    {"pattern": "bge-", "mmlu_pro": 0.0, "human_eval": 0.0, "ttft_ms": 20},
]


def fuzzy_enrich_benchmarks(model_id: str, developer: str = "") -> Dict[str, float]:
    """Fuzzy cross-reference a model identifier against the benchmark DB.

    Matches case-insensitive substrings of ``model_id`` against
    ``FUZZY_BENCHMARK_PATTERNS`` in priority order (most specific first). When a
    match is found, the corresponding MMLU-Pro, HumanEval, and TTFT figures are
    returned. Unknown niche derivatives inherit the closest base-family tier;
    truly unknown identifiers return an empty dict so callers leave the columns
    untouched (rendered as ``-``).

    Args:
        model_id (str): Model identifier to cross-reference.
        developer (str): Optional releasing organization hint.

    Returns:
        dict: ``{"mmlu_pro", "human_eval", "ttft_ms"}`` when matched, else ``{}``.
    """
    normalized = (model_id or "").lower()
    for entry in FUZZY_BENCHMARK_PATTERNS:
        pattern = entry["pattern"].lower()
        if entry.get("token"):
            matched = re.search(
                r"(?<![a-z0-9])" + re.escape(pattern) + r"(?![a-z0-9])", normalized
            ) is not None
        else:
            matched = pattern in normalized
        if matched:
            return {
                "mmlu_pro": float(entry["mmlu_pro"]),
                "human_eval": float(entry["human_eval"]),
                "ttft_ms": float(entry["ttft_ms"]),
            }
    return {}


class ModelBenchmarkClient:
    """Scientific benchmark client with a local cache and role-based pairing.

    Attributes:
        cache_path (str): Filesystem path of the benchmark JSON cache.
    """

    def __init__(self, cache_path: Optional[str] = None) -> None:
        self.cache_path = cache_path or DEFAULT_CACHE_PATH
        self._records: List[Dict[str, Any]] = []
        self._last_refreshed: Optional[str] = None
        self._load_cache()

    # ------------------------------------------------------------------
    # -- Cache lifecycle ----------------------------------------------
    # ------------------------------------------------------------------

    def _load_cache(self) -> None:
        """Load the benchmark cache, seeding defaults when absent or corrupt."""
        self._records = list(DEFAULT_BENCHMARKS)
        try:
            with open(self.cache_path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            records = payload.get("records") or payload.get("models")
            if isinstance(records, list) and records:
                self._records = records
            self._last_refreshed = payload.get("last_refreshed")
        except (OSError, ValueError):
            self._ensure_cache()

    def _save_cache(self) -> None:
        """Persist the benchmark cache atomically in pure UTF-8."""
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            payload = {
                "schema_version": "1.0",
                "source": "talos_model_benchmark_client",
                "last_refreshed": self._last_refreshed,
                "records": self._records,
            }
            tmp_path = self.cache_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.cache_path)
        except OSError:
            pass

    def _ensure_cache(self) -> None:
        """Create the cache directory and seed the file when absent."""
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            if not os.path.exists(self.cache_path):
                self._save_cache()
        except OSError:
            pass

    # ------------------------------------------------------------------
    # -- Discovery and refresh -----------------------------------------
    # ------------------------------------------------------------------

    def refresh(self, online: bool = True) -> Dict[str, Any]:
        """Refresh the benchmark store and return a summary dictionary.

        Args:
            online (bool): When True, attempt a best-effort remote scrape that
                degrades to the static seed on any failure. When False, simply
                re-persist the curated seed (pure air-gapped operation).

        Returns:
            dict: Summary with ``record_count``, ``mode``, and ``cache_path``.
        """
        mode = "air_gapped_seed"
        if online:
            fetched = self._fetch_remote_benchmarks()
            if fetched:
                self._merge_records(fetched)
                mode = "live_scrape_merged"
        self._last_refreshed = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._save_cache()
        return {
            "record_count": len(self._records),
            "mode": mode,
            "cache_path": self.cache_path,
        }

    def _fetch_remote_benchmarks(self) -> List[Dict[str, Any]]:
        """Best-effort remote scrape; returns an empty list when unavailable.

        This method honours the 100 percent air-gapped mandate: any network
        error, timeout, or malformed payload yields an empty result and the
        caller falls back to the curated seed.
        """
        try:
            import requests
        except ImportError:
            return []
        sources = [
            "https://raw.githubusercontent.com/your-org/talos-benchmarks/main/llm_benchmarks.json",
        ]
        for url in sources:
            try:
                resp = requests.get(url, timeout=5.0)
                if resp.status_code != 200:
                    continue
                payload = resp.json()
                records = payload.get("records") or payload.get("models")
                if isinstance(records, list):
                    return records
            except Exception:
                continue
        return []

    def _merge_records(self, records: List[Dict[str, Any]]) -> None:
        """Merge fetched records by model name, never dropping seeds."""
        existing = {r.get("model"): r for r in self._records}
        for record in records:
            if isinstance(record, dict) and record.get("model"):
                existing[record["model"]] = record
        self._records = list(existing.values())

    def ingest_remote_records(self, records: List[Dict[str, Any]]) -> int:
        """Merge remote worker records and persist, returning the new-model count.

        Args:
            records (list[dict]): Model records from a remote JSONL buffer.

        Returns:
            int: Number of genuinely new model identifiers merged.
        """
        existing = {r.get("model") for r in self._records}
        new_count = sum(
            1
            for r in records
            if isinstance(r, dict) and r.get("model") and r.get("model") not in existing
        )
        self._merge_records(records)
        self._last_refreshed = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._save_cache()
        return new_count

    # ------------------------------------------------------------------
    # -- Role-based top-model pairing ----------------------------------
    # ------------------------------------------------------------------

    def get_top_models_by_role(self) -> Dict[str, Dict[str, Any]]:
        """Return the optimal model pairing for each of the four roles.

        Returns:
            dict: Role key to a dictionary with the top model, provider, and
                benchmark figures.
        """
        sorters: Dict[str, tuple] = {
            "fast_screening": (lambda r: r.get("ttft_ms", 10**9), False),
            "rigorous_audit": (lambda r: r.get("mmlu_pro", 0.0), True),
            "code_audit": (lambda r: r.get("human_eval", 0.0), True),
            "vector_embeddings": (lambda r: r.get("throughput_tps", 0.0), True),
        }
        result: Dict[str, Dict[str, Any]] = {}
        for role, (key, reverse) in sorters.items():
            candidates = [r for r in self._records if role in r.get("roles", [])]
            candidates.sort(key=key, reverse=reverse)
            top = candidates[0] if candidates else {}
            result[role] = {
                "role": role,
                "title": ROLE_TITLES.get(role, role),
                "model": top.get("model", ""),
                "provider": top.get("provider", ""),
                "mmlu_pro": top.get("mmlu_pro", 0.0),
                "human_eval": top.get("human_eval", 0.0),
                "cost_per_1m_usd": top.get("cost_per_1m_usd", 0.0),
                "ttft_ms": top.get("ttft_ms", 0.0),
                "throughput_tps": top.get("throughput_tps", 0.0),
            }
        return result

    def reconcile_local_budget(self) -> Dict[str, Dict[str, str]]:
        """Reconcile cloud recommendations with the local RTX 4070 budget.

        Delegates to the hardware advisor (imported lazily) to obtain the local
        recommended model per role, then joins it with the hardware advisor's
        cloud pairing. Returns an empty mapping on any failure so this method
        never crashes an air-gapped or CPU-only session.

        Returns:
            dict: Role key to ``{"local_recommended", "cloud"}``.
        """
        mapping = {
            "fast_screening": "fast_screening",
            "rigorous_audit": "deep_reasoning_rigor",
            "code_audit": "code_audit_slicing",
            "vector_embeddings": "vector_embeddings",
        }
        try:
            from src.core.hardware_advisor import HardwareModelAdvisor
            matrix = HardwareModelAdvisor().get_role_based_matrix()
            roles = {r["role"]: r for r in matrix["roles"]}
        except Exception:
            return {}
        local_map: Dict[str, Dict[str, str]] = {}
        for role_key, advisor_key in mapping.items():
            info = roles.get(advisor_key, {})
            local_map[role_key] = {
                "local_recommended": info.get("local_recommended", ""),
                "cloud": info.get("cloud", ""),
            }
        return local_map

    # ------------------------------------------------------------------
    # -- Rendering -----------------------------------------------------
    # ------------------------------------------------------------------

    def render_discovery_table(self) -> None:
        """Render the benchmark discovery matrix as a styled Rich table."""
        try:
            from rich.console import Console
            from rich.table import Table
        except ImportError:
            self._render_plain()
            return

        top = self.get_top_models_by_role()
        local_map = self.reconcile_local_budget()

        console = Console()
        table = Table(
            title="TALOS SOTA Model Discovery Matrix (v5.22.1)",
            header_style="bold bright_cyan",
            border_style="cyan",
        )
        table.add_column("Role", style="bold white")
        table.add_column("Top Model (Cloud)", style="bright_blue")
        table.add_column("Provider", style="cyan")
        table.add_column("MMLU-Pro", justify="right")
        table.add_column("HumanEval", justify="right")
        table.add_column("TTFT (ms)", justify="right")
        table.add_column("Cost $/1M", justify="right")
        table.add_column("Local (RTX 4070)", style="bright_green")

        for role, info in top.items():
            local = local_map.get(role, {}).get("local_recommended", "-")
            table.add_row(
                info["title"],
                info["model"] or "-",
                info["provider"] or "-",
                f"{info['mmlu_pro']:.1f}",
                f"{info['human_eval']:.1f}",
                f"{info['ttft_ms']:.0f}",
                f"{info['cost_per_1m_usd']:.2f}",
                local or "-",
            )
        console.print(table)

    def _render_plain(self) -> None:
        """Fallback plain-text renderer when Rich is unavailable."""
        top = self.get_top_models_by_role()
        local_map = self.reconcile_local_budget()
        for role, info in top.items():
            local = local_map.get(role, {}).get("local_recommended", "-")
            print(
                f"{info['title']}: {info['model']} ({info['provider']}) "
                f"| MMLU-Pro {info['mmlu_pro']} | HumanEval {info['human_eval']} "
                f"| TTFT {info['ttft_ms']}ms | ${info['cost_per_1m_usd']}/1M "
                f"| Local: {local}"
            )


def run_discover_llms(online: bool = True) -> int:
    """Refresh the benchmark store and render the discovery matrix.

    This is the entry point behind ``python talos.py --discover-llms``.

    Args:
        online (bool): Whether to attempt a live scrape before rendering.

    Returns:
        int: Process exit code (0 on success).
    """
    client = ModelBenchmarkClient()
    client.refresh(online=online)
    client.render_discovery_table()
    return 0



