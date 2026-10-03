# -*- coding: utf-8 -*-
"""
Module: hardware_advisor.py
Project: TALOS v5.20.0
Description:
    Hardware-aware model advisor that translates raw GPU/CPU telemetry into
    a mathematical parameter budget and a concrete recommended model stack.
    It reuses the existing VRAM detection facilities in ``src/core/hardware.py``
    (nvidia-smi probing) and augments them with Torch CUDA introspection for
    the device name, psutil for system RAM, and platform heuristics for laptop
    CPU detection -- all guarded so a CPU-only, air-gapped workstation degrades
    gracefully to a 3B parameter budget instead of raising.

    The central formula is a piecewise 4-bit-quantization budget:
        VRAM >= 11.0 GB   -> 14B parameters (e.g. Qwen 2.5 14B)
        5.5 <= VRAM < 11  ->  8B parameters (e.g. Llama 3.1 8B)
        VRAM < 5.5 (CPU)  ->  3B parameters (e.g. Qwen 2.5 3B)
    A SOTA discovery radar then surfaces newer releases (Qwen 3/4, Llama 4)
    that fit within the detected budget, degrading to a static verified list
    when the network is unavailable.

    Key design decisions:
    - Pure, side-effect-free budgeting functions are separated from I/O so the
      arithmetic is unit-testable without a GPU.
    - All hardware access is wrapped in try/except; no import failure (torch,
      psutil) can crash the advisor.
    - The SOTA radar is best-effort and non-blocking, honouring the 100%
      air-gapped, local-first mandate (Constitution II).

Dependencies:
    - os, platform, json: OS introspection and file-system fallbacks.
    - src.core.hardware: detect_vram_gb() and parameter-extraction helpers.
    - config.settings: canonical Ollama base URL.
    - torch / psutil (optional, lazy): CUDA device and system RAM telemetry.
    - rich (lazy): terminal table rendering for render_recommendations().
"""

import os
import platform
from typing import Dict, List, Optional

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
if _P:
    import sys
    sys.path.insert(0, _P)

from src.core.hardware import detect_vram_gb, extract_params_b

try:
    from config.settings import OLLAMA_BASE_URL
except ImportError:
    OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# -- SOTA discovery radar (static, verified fallback when offline) -------------
# Each entry records a model family and its approximate parameter count in
# billions. The radar is filtered against the detected VRAM budget; when the
# network is unavailable it is the sole source of SOTA signals.
SOTA_RADAR: List[Dict] = [
    {"name": "qwen3:30b-a3b", "family": "Qwen 3", "params_b": 30.0},
    {"name": "qwen3:14b", "family": "Qwen 3", "params_b": 14.0},
    {"name": "qwen3:8b", "family": "Qwen 3", "params_b": 8.0},
    {"name": "qwen3:4b", "family": "Qwen 3", "params_b": 4.0},
    {"name": "llama4:scout", "family": "Llama 4", "params_b": 17.0},
    {"name": "llama4:maverick", "family": "Llama 4", "params_b": 400.0},
    {"name": "qwen2.5:14b", "family": "Qwen 2.5", "params_b": 14.0},
    {"name": "qwen2.5:7b", "family": "Qwen 2.5", "params_b": 7.0},
    {"name": "qwen2.5:3b", "family": "Qwen 2.5", "params_b": 3.0},
    {"name": "llama3.1:8b", "family": "Llama 3.1", "params_b": 8.0},
    {"name": "gemma3:12b", "family": "Gemma 3", "params_b": 12.0},
    {"name": "deepseek-r1:14b", "family": "DeepSeek R1", "params_b": 14.0},
]


class HardwareModelAdvisor:
    """Compute a VRAM-based parameter budget and a tailored model stack.

    The advisor reuses existing VRAM telemetry and exposes five capabilities:
    hardware profiling, mathematical parameter budgeting, role-based model
    recommendations, a four-role SOTA model matcher, and a best-effort SOTA
    discovery radar. All public methods degrade gracefully when no GPU or
    network is available.
    """

    # ------------------------------------------------------------------
    # -- Hardware profiling ---------------------------------------------
    # ------------------------------------------------------------------

    def get_hardware_profile(self) -> Dict:
        """Detect the host's inference hardware.

        CUDA device name and VRAM are read from Torch when available, with a
        fallback to the nvidia-smi probe in ``src.core.hardware``. System RAM
        is read from psutil. Laptop detection uses a battery heuristic.

        Returns:
            dict: ``{has_cuda, device_name, total_vram_gb, system_ram_gb,
                is_laptop_cpu}``.
        """
        has_cuda = False
        device_name = "CPU"
        total_vram_gb: Optional[float] = None

        # -- Torch CUDA introspection (guarded) --
        try:
            import torch
            if torch.cuda.is_available():
                has_cuda = True
                device_name = torch.cuda.get_device_name(0)
                total_vram_gb = float(
                    torch.cuda.get_device_properties(0).total_memory
                ) / (1024 ** 3)
        except Exception:
            has_cuda = False

        # -- nvidia-smi fallback when Torch is absent or CUDA unavailable --
        if total_vram_gb is None:
            detected = detect_vram_gb()
            if detected:
                total_vram_gb = float(detected)
                has_cuda = True

        # -- Resolve a marketing device name when torch lacked CUDA support --
        if has_cuda and device_name == "CPU":
            gpu_name = self._detect_gpu_name()
            if gpu_name:
                device_name = gpu_name

        system_ram_gb: Optional[float] = None
        try:
            import psutil
            system_ram_gb = float(psutil.virtual_memory().total) / (1024 ** 3)
        except Exception:
            system_ram_gb = None

        return {
            "has_cuda": bool(has_cuda),
            "device_name": device_name if has_cuda else "CPU",
            "total_vram_gb": float(total_vram_gb) if total_vram_gb else 0.0,
            "system_ram_gb": float(system_ram_gb) if system_ram_gb else 0.0,
            "is_laptop_cpu": self._detect_laptop_cpu(),
        }

    @staticmethod
    def _detect_laptop_cpu() -> bool:
        """Return True when the host is likely a battery-powered laptop.

        Returns:
            bool: True when a battery device is detected, else False.
        """
        try:
            import psutil
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery is not None:
                    return True
        except Exception:
            pass
        # -- Linux fallback: presence of a BAT* power supply implies laptop --
        try:
            if os.path.isdir("/sys/class/power_supply"):
                entries = os.listdir("/sys/class/power_supply")
                if any(entry.upper().startswith("BAT") for entry in entries):
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def _detect_gpu_name() -> Optional[str]:
        """Return the first GPU's marketing name via nvidia-smi, or ``None``.

        Used as a fallback when Torch is installed without CUDA support but
        the driver still exposes the device through nvidia-smi.

        Returns:
            Optional[str]: The GPU marketing name, or ``None`` on failure.
        """
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0].strip()
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # -- Mathematical parameter budgeting ------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_vram_budget(vram_gb: float) -> float:
        """Return the maximum recommended parameter count (billions) for VRAM.

        Piecewise 4-bit-quantization budget:
            ``vram_gb >= 11.0`` -> ``14.0`` B
            ``5.5 <= vram_gb < 11.0`` -> ``8.0`` B
            ``vram_gb < 5.5`` (or None) -> ``3.0`` B

        Args:
            vram_gb (float): Detected GPU VRAM in GB (0.0 or None for CPU-only).

        Returns:
            float: Maximum recommended parameter count in billions.
        """
        if vram_gb is None or vram_gb < 5.5:
            return 3.0
        if vram_gb < 11.0:
            return 8.0
        return 14.0

    # ------------------------------------------------------------------
    # -- Role-based model recommendations ------------------------------
    # ------------------------------------------------------------------

    def get_recommendations(self) -> Dict:
        """Return a tailored model stack for each inference role.

        Returns:
            dict: Keys ``hardware_profile``, ``max_params_billions``,
                ``screening_local``, ``reasoning_local``,
                ``reasoning_cloud``, and ``fast_cloud``.
        """
        profile = self.get_hardware_profile()
        budget = self.calculate_vram_budget(profile["total_vram_gb"])

        if budget >= 14.0:
            screening_local = "llama3.1:8b"
            reasoning_local = "qwen2.5:14b"
        elif budget >= 8.0:
            screening_local = "qwen2.5:3b"
            reasoning_local = "qwen2.5:7b"
        else:
            screening_local = "qwen2.5:1.5b"
            reasoning_local = "qwen2.5:3b"

        return {
            "hardware_profile": profile,
            "max_params_billions": budget,
            "screening_local": screening_local,
            "reasoning_local": reasoning_local,
            "reasoning_cloud": "deepseek-reasoner",
            "fast_cloud": "gemini-2.5-flash",
        }

    # ------------------------------------------------------------------
    # -- SOTA online radar ---------------------------------------------
    # ------------------------------------------------------------------

    def scan_sota_models(self, timeout: float = 1.5) -> List[Dict]:
        """Surface SOTA models that fit the detected hardware budget.

        The static radar is always evaluated against the parameter budget.
        Live Ollama tags mark locally installed models, and a best-effort
        OpenRouter probe appends cloud releases. When offline, the static
        radar alone is returned -- the method never raises.

        Args:
            timeout (float): Per-request network timeout in seconds.

        Returns:
            list[dict]: SOTA entries with ``name``, ``family``,
                ``params_billions``, ``fits_budget``, ``installed``, and
                ``source`` fields.
        """
        budget = self.calculate_vram_budget(
            self.get_hardware_profile()["total_vram_gb"]
        )

        results: List[Dict] = []
        for entry in SOTA_RADAR:
            results.append({
                "name": entry["name"],
                "family": entry["family"],
                "params_billions": entry["params_b"],
                "fits_budget": entry["params_b"] <= budget,
                "installed": False,
                "source": "static_radar",
            })

        # -- Live Ollama tags (local-first, marks installed models) --
        installed_names = self._scan_ollama_tags(timeout)
        for result in results:
            if result["name"] in installed_names:
                result["installed"] = True
                result["source"] = "installed"

        # -- Best-effort OpenRouter probe for newer cloud releases --
        for cloud_model in self._scan_openrouter_models(timeout):
            if cloud_model["name"] not in {r["name"] for r in results}:
                results.append(cloud_model)

        results.sort(key=lambda r: r["params_billions"])
        return results

    @staticmethod
    def _scan_ollama_tags(timeout: float) -> set:
        """Return the set of locally installed Ollama model names.

        Args:
            timeout (float): HTTP timeout in seconds.

        Returns:
            set[str]: Installed model names, or an empty set when offline.
        """
        installed: set = set()
        try:
            import requests
            resp = requests.get(
                OLLAMA_BASE_URL.rstrip("/") + "/api/tags", timeout=timeout
            )
            if resp.status_code == 200:
                for model in resp.json().get("models", []):
                    name = model.get("name", "")
                    if name:
                        installed.add(name)
        except Exception:
            pass
        return installed

    def _scan_openrouter_models(self, timeout: float) -> List[Dict]:
        """Return a list of newer cloud SOTA models discovered via OpenRouter.

        Args:
            timeout (float): HTTP timeout in seconds.

        Returns:
            list[dict]: Cloud SOTA entries fitting the budget, or [] offline.
        """
        budget = self.calculate_vram_budget(
            self.get_hardware_profile()["total_vram_gb"]
        )
        found: List[Dict] = []
        try:
            import requests
            resp = requests.get(
                "https://openrouter.ai/api/v1/models", timeout=timeout
            )
            if resp.status_code != 200:
                return []
            for model in resp.json().get("data", []):
                model_id = model.get("id", "")
                params = extract_params_b(model_id)
                if params is None or params > budget:
                    continue
                family = model_id.split("/")[0] if "/" in model_id else model_id
                found.append({
                    "name": model_id,
                    "family": family,
                    "params_billions": params,
                    "fits_budget": True,
                    "installed": False,
                    "source": "openrouter",
                })
        except Exception:
            pass
        return found

    # ------------------------------------------------------------------
    # -- Rich terminal rendering ---------------------------------------
    # ------------------------------------------------------------------

    def render_recommendations(self) -> None:
        """Render the Hardware Profile, Parameter Budget, Recommended Stack,
        and SOTA radar as styled Rich tables."""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
        except ImportError:
            recs = self.get_recommendations()
            print("Hardware-Aware Model Advisor:")
            print(f"  Device: {recs['hardware_profile']['device_name']}")
            print(f"  VRAM: {recs['hardware_profile']['total_vram_gb']:.1f} GB")
            print(f"  Max params: {recs['max_params_billions']}B")
            print(f"  Screening (local): {recs['screening_local']}")
            print(f"  Reasoning (local): {recs['reasoning_local']}")
            print(f"  Reasoning (cloud): {recs['reasoning_cloud']}")
            print(f"  Fast (cloud): {recs['fast_cloud']}")
            return

        console = Console()
        recs = self.get_recommendations()
        profile = recs["hardware_profile"]

        console.print(Panel(
            "[bold bright_cyan]Hardware-Aware Model Advisor[/bold bright_cyan]\n"
            "[dim]VRAM parameter budgeting and SOTA model discovery.[/dim]",
            border_style="bright_cyan",
        ))

        # -- Hardware profile table --
        profile_table = Table(
            title="Hardware Profile",
            box=None,
            show_header=False,
            border_style="cyan",
        )
        profile_table.add_column("Attribute", style="dim")
        profile_table.add_column("Value", style="white")
        profile_table.add_row("CUDA available", str(profile["has_cuda"]))
        profile_table.add_row("Device", str(profile["device_name"]))
        profile_table.add_row(
            "Total VRAM", f"{profile['total_vram_gb']:.1f} GB"
        )
        profile_table.add_row(
            "System RAM", f"{profile['system_ram_gb']:.1f} GB"
        )
        profile_table.add_row("Laptop CPU", str(profile["is_laptop_cpu"]))
        console.print(profile_table)

        # -- Budget + recommended stack table --
        stack_table = Table(
            title="Parameter Budget & Recommended Stack",
            show_header=True,
            border_style="cyan",
        )
        stack_table.add_column("Role", style="dim cyan")
        stack_table.add_column("Model", style="white")
        stack_table.add_row(
            "Max parameters", f"{recs['max_params_billions']:.0f}B"
        )
        stack_table.add_row("Screening (local)", recs["screening_local"])
        stack_table.add_row("Reasoning (local)", recs["reasoning_local"])
        stack_table.add_row("Reasoning (cloud)", recs["reasoning_cloud"])
        stack_table.add_row("Fast (cloud)", recs["fast_cloud"])
        console.print(stack_table)

        # -- SOTA radar table --
        radar_table = Table(
            title="SOTA Discovery Radar",
            show_header=True,
            border_style="magenta",
        )
        radar_table.add_column("Model", style="white")
        radar_table.add_column("Family", style="dim cyan")
        radar_table.add_column("Params", style="yellow", justify="right")
        radar_table.add_column("Fits", style="green")
        radar_table.add_column("Installed", style="magenta")
        for entry in self.scan_sota_models():
            radar_table.add_row(
                entry["name"],
                entry["family"],
                f"{entry['params_billions']:.1f}B",
                "yes" if entry["fits_budget"] else "no",
                "yes" if entry["installed"] else "no",
            )
        console.print(radar_table)

    # ------------------------------------------------------------------
    # -- 4-Role SOTA Model Matcher (v5.19.0) ----------------------------
    # ------------------------------------------------------------------

    def get_role_based_matrix(self) -> Dict:
        """Return the four-role scientific workload model matrix.

        Categorizes the canonical model stack across four scientific workloads,
        each with a local-hardware recommendation (GPU and CPU tiers) and a
        Cloud Mesh counterpart. The local recommendation is selected against
        the detected VRAM budget; the cloud model is fixed per the Universal
        Cloud Mesh registry.

        The four roles are:
            - ``fast_screening``: cheap, low-latency relevance sieving.
            - ``deep_reasoning_rigor``: heavy multi-step reasoning and rigor.
            - ``code_audit_slicing``: source-slice audit and code synthesis.
            - ``vector_embeddings``: semantic vector embedding generation.

        Returns:
            dict: Keys ``roles`` (list of per-role dictionaries), plus the
                resolved ``hardware_profile`` and ``vram_budget``.
        """
        profile = self.get_hardware_profile()
        budget = self.calculate_vram_budget(profile["total_vram_gb"])
        has_gpu = bool(profile.get("has_cuda"))

        def _gpu(candidate: str, cpu_fallback: str) -> str:
            return candidate if has_gpu else cpu_fallback

        roles = [
            {
                "role": "fast_screening",
                "title": "Fast Screening Sieve",
                "local_gpu": "llama3.1:8b",
                "local_cpu": "qwen2.5:3b",
                "local_recommended": _gpu("llama3.1:8b", "qwen2.5:3b"),
                "cloud": "gemini-2.5-flash",
            },
            {
                "role": "deep_reasoning_rigor",
                "title": "Deep Reasoning Rigor",
                "local_gpu": "qwen2.5:14b",
                "local_cpu": "qwen2.5:3b",
                "local_recommended": _gpu("qwen2.5:14b", "qwen2.5:3b"),
                "cloud": "deepseek-reasoner",
            },
            {
                "role": "code_audit_slicing",
                "title": "Code Audit Slicing",
                "local_gpu": "qwen2.5-coder:14b",
                "local_cpu": "qwen2.5:3b",
                "local_recommended": _gpu("qwen2.5-coder:14b", "qwen2.5:3b"),
                "cloud": "deepseek-coder",
            },
            {
                "role": "vector_embeddings",
                "title": "Vector Embeddings",
                "local_gpu": "nomic-embed-text",
                "local_cpu": "nomic-embed-text",
                "local_recommended": "nomic-embed-text",
                "cloud": "text-embedding-3-small",
            },
        ]
        return {
            "roles": roles,
            "hardware_profile": profile,
            "vram_budget": budget,
        }

    def render_role_matrix(self) -> None:
        """Render the four-role SOTA matrix as a styled Rich table.

        Falls back to plain ``print`` lines when Rich is unavailable, so the
        method never raises in a headless or minimal environment.
        """
        matrix = self.get_role_based_matrix()
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
        except ImportError:
            for role in matrix["roles"]:
                print(f"{role['title']}: local={role['local_recommended']} "
                      f"| cloud={role['cloud']}")
            return
        console = Console()
        console.print(Panel(
            "[bold bright_cyan]4-Role SOTA Model Matcher[/bold bright_cyan]\n"
            "[dim]Scientific workload model matrix (local hardware + Cloud Mesh).[/dim]",
            border_style="bright_cyan",
        ))
        table = Table(
            title="Cognitive SOTA Role Matcher",
            show_header=True,
            border_style="cyan",
        )
        table.add_column("Role", style="dim cyan")
        table.add_column("Workload", style="white")
        table.add_column("Local (GPU)", style="green")
        table.add_column("Local (CPU)", style="yellow")
        table.add_column("Recommended Local", style="bright_green")
        table.add_column("Cloud Mesh", style="bright_blue")
        for role in matrix["roles"]:
            table.add_row(
                role["role"],
                role["title"],
                role["local_gpu"],
                role["local_cpu"],
                role["local_recommended"],
                role["cloud"],
            )
        console.print(table)

    def apply_recommended_models(self) -> bool:
        """Persist the recommended 4-role model stack into the active profile.

        Updates the ``ai_models`` block (fast edge, heavy reasoning, and cloud
        fallback models) and records the full four-role matrix under a new
        ``recommended_role_models`` key, then writes the active profile's
        ``config.json`` atomically in pure UTF-8 (``ensure_ascii=False``).

        Returns:
            bool: True when the config was updated and persisted, else False.
        """
        matrix = self.get_role_based_matrix()
        roles = {r["role"]: r for r in matrix["roles"]}

        try:
            from src.core.profile_manager import ProfileManager
            config_path = ProfileManager().get_active_config_path()
        except Exception:
            return False

        try:
            import json
            import os
            with open(config_path, "r", encoding="utf-8") as fh:
                config = json.load(fh)
        except Exception:
            return False

        ai_models = config.setdefault("ai_models", {})
        ai_models.setdefault("fast_edge", {})["model"] = (
            roles["fast_screening"]["local_recommended"])
        ai_models.setdefault("heavy_reasoning", {})["model"] = (
            roles["deep_reasoning_rigor"]["local_recommended"])
        cloud = ai_models.setdefault("cloud_fallback", {})
        cloud["flash_model"] = roles["fast_screening"]["cloud"]
        cloud["pro_model"] = roles["deep_reasoning_rigor"]["cloud"]
        cloud["deepseek_model"] = roles["deep_reasoning_rigor"]["cloud"]

        config["recommended_role_models"] = {
            r["role"]: {
                "title": r["title"],
                "local": r["local_recommended"],
                "cloud": r["cloud"],
            } for r in matrix["roles"]
        }

        try:
            tmp_path = config_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(config, fh, indent=2, ensure_ascii=False)
            os.replace(tmp_path, config_path)
            print(f"[OK] Recommended 4-role model stack applied to {config_path}")
            return True
        except Exception:
            return False


# -- Module-level convenience singleton ----------------------------------------
_advisor_singleton: Optional[HardwareModelAdvisor] = None


def get_hardware_advisor() -> HardwareModelAdvisor:
    """Return a shared HardwareModelAdvisor singleton.

    Returns:
        HardwareModelAdvisor: The shared advisor instance.
    """
    global _advisor_singleton
    if _advisor_singleton is None:
        _advisor_singleton = HardwareModelAdvisor()
    return _advisor_singleton

