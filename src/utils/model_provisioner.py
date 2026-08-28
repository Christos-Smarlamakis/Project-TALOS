# -*- coding: utf-8 -*-
"""
Module: model_provisioner.py
Project: TALOS v5.10.5
Description:
    Universal Dynamic Model Provisioner for the TALOS LLM tiers. Provides a
    single deterministic entry point for guaranteeing that an inference model is
    available before it is routed to. The provisioner detects the delivery
    protocol of a model name (Ollama, HuggingFace Hub, or a cloud provider),
    resolves any pre-existing local copy (honoring FAST_EDGE_MODEL_PATH), and
    just-in-time provisions missing models with a self-healing fallback cascade
    that never crashes the caller on network or disk failure.

    Key design decisions:
    - Local-first and air-gapped by default (Constitution II): FAST_EDGE_MODEL_PATH
      and the in-tree models/ directory are checked before any network download.
    - Protocol detection is deterministic: cloud prefixes are matched first, then
      Ollama (colon), then HuggingFace Hub (forward slash).
    - The HuggingFace Hub client is imported optionally so the module remains
      importable in environments where huggingface_hub is not installed.
    - Self-healing fallback: every provisioning failure is caught, logged with a
      formal warning, and reported as a boolean False without raising.

Dependencies:
    - os, sys, re, subprocess, argparse: Standard library utilities.
    - pathlib.Path: Project-root and model-directory resolution.
    - dotenv.load_dotenv: Reads FAST_EDGE_MODEL_PATH and related keys from .env.
    - src.utils.logger.get_logger: Structured console and file logging.
    - huggingface_hub.snapshot_download (optional): HuggingFace Hub downloads.
"""
import os
import re
import sys
import subprocess
import argparse
import functools

from pathlib import Path

# -- Resolve the project root (same pattern as all src/*.py modules) ----------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

PROJECT_ROOT = _P

# -- Load .env so FAST_EDGE_MODEL_PATH and API keys are visible via os.environ -
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:
    load_dotenv = None

# -- Optional HuggingFace Hub client (graceful degradation) -------------------
try:
    from huggingface_hub import snapshot_download as _hf_snapshot_download
    HUGGINGFACE_HUB_AVAILABLE = True
except ImportError:
    _hf_snapshot_download = None
    HUGGINGFACE_HUB_AVAILABLE = False

# -- Canonical configuration defaults -----------------------------------------
try:
    from config.settings import FAST_EDGE_MODEL, HEAVY_REASONING_MODEL
except ImportError:
    FAST_EDGE_MODEL = "fermionresearch/Neutrino-8B"
    HEAVY_REASONING_MODEL = "qwen2.5:14b"

# -- Structured logging via the canonical logger factory ----------------------
from src.utils.logger import get_logger

logger = get_logger("model_provisioner")


class ModelProvisioner:
    """Universal model provisioner with deterministic protocol detection and a
    self-healing, local-first resolution cascade.

    Attributes:
        project_root (Path): Resolved TALOS project root directory.
        models_dir (Path): Directory used for HuggingFace Hub snapshots.
    """

    # Cloud provider prefixes matched case-insensitively. Checked before the
    # generic colon / slash rules so provider-qualified names such as "nvidia/"
    # or "groq:" are never mistaken for local models.
    CLOUD_PREFIXES = (
        "gemini-", "nvidia/", "groq:", "cerebras:", "github:", "github/",
        "mistral-", "openrouter/", "deepseek-", "deepseek:", "gpt-", "claude-",
        "openai/", "anthropic/",
    )

    # Environment variable holding the API key for each cloud prefix.
    CLOUD_KEY_MAP = {
        "gemini-": "GEMINI_API_KEY",
        "nvidia/": "NVIDIA_API_KEY",
        "groq:": "GROQ_API_KEY",
        "cerebras:": "CEREBRAS_API_KEY",
        "github:": "GITHUB_API_KEY",
        "github/": "GITHUB_API_KEY",
        "mistral-": "MISTRAL_API_KEY",
        "openrouter/": "OPENROUTER_API_KEY",
        "deepseek-": "DEEPSEEK_API_KEY",
        "deepseek:": "DEEPSEEK_API_KEY",
        "gpt-": "OPENAI_API_KEY",
        "claude-": "ANTHROPIC_API_KEY",
        "openai/": "OPENAI_API_KEY",
        "anthropic/": "ANTHROPIC_API_KEY",
    }

    def __init__(self, project_root=None, models_dir=None):
        self.project_root = Path(project_root) if project_root else Path(PROJECT_ROOT)
        self.models_dir = Path(models_dir) if models_dir else (self.project_root / "models")

    # ------------------------------------------------------------------
    # -- Protocol detection --------------------------------------------
    # ------------------------------------------------------------------

    @functools.lru_cache(maxsize=512)
    def detect_protocol(self, model_name):
        """Return the delivery protocol for a model name.

        Args:
            model_name (str): The model identifier to classify.

        Returns:
            str: One of "cloud", "ollama", or "huggingface".
        """
        name = (model_name or "").strip()
        lowered = name.lower()

        # -- Cloud providers win: provider-qualified names are never local ----
        for prefix in self.CLOUD_PREFIXES:
            if lowered.startswith(prefix):
                return "cloud"

        # -- Ollama models carry a tag colon (e.g. qwen2.5:14b) ---------------
        if ":" in name:
            return "ollama"

        # -- HuggingFace Hub repos carry an org/repo slash ---------------------
        if "/" in name:
            return "huggingface"

        # -- Local-first default: untagged names are treated as Ollama models --
        return "ollama"

    # ------------------------------------------------------------------
    # -- Local path resolution -----------------------------------------
    # ------------------------------------------------------------------

    @functools.lru_cache(maxsize=1024)
    def _sanitize(self, model_name):
        """Convert a model name into a filesystem-safe directory name."""
        return re.sub(r"[^A-Za-z0-9._-]", "_", (model_name or "").strip())

    def _has_valid_artifacts(self, directory):
        """Return True when a directory contains at least one model artifact."""
        directory = Path(directory)
        if not directory.is_dir():
            return False
        for entry in directory.iterdir():
            if entry.is_file():
                return True
        return False

    def resolve_local_model_path(self, model_name):
        """Resolve a pre-existing local copy of a model, or None.

        Priority 1: FAST_EDGE_MODEL_PATH from the environment / .env.
        Priority 2: models/<sanitized_model_name> inside the project root.
        Priority 3: None (which triggers a network download).

        Args:
            model_name (str): The model identifier to resolve.

        Returns:
            Optional[str]: Absolute path to a local model directory, or None.
        """
        # -- Priority 1: FAST_EDGE_MODEL_PATH (strict local override) ---------
        env_path = os.environ.get("FAST_EDGE_MODEL_PATH", "")
        if env_path:
            candidate = Path(env_path)
            if candidate.is_dir():
                logger.info("Local model path resolved via FAST_EDGE_MODEL_PATH: %s", candidate)
                return str(candidate)

        # -- Priority 2: in-tree models/<sanitized_name> ----------------------
        local_dir = self.models_dir / self._sanitize(model_name)
        if local_dir.is_dir() and self._has_valid_artifacts(local_dir):
            logger.info("Local model path resolved via models/ tree: %s", local_dir)
            return str(local_dir)

        # -- Priority 3: no local copy found ---------------------------------
        return None
    # ------------------------------------------------------------------
    # -- Ollama helpers ------------------------------------------------
    # ------------------------------------------------------------------

    def _ollama_list(self):
        """Return the set of model names reported by `ollama list`."""
        try:
            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True,
                check=False, timeout=10,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            logger.warning("Ollama list query failed or timed out. Assuming no models installed.")
            return set()
        names = set()
        lines = (result.stdout or "").splitlines()
        for line in lines[1:]:  # skip the NAME/ID/SIZE header row
            token = line.split()[0] if line.split() else ""
            if token:
                names.add(token)
        return names

    def _ollama_has_model(self, model_name):
        """Return True when the model (or its :latest tag) is installed."""
        installed = self._ollama_list()
        candidates = {model_name, model_name + ":latest"}
        return bool(installed & candidates)

    def _ollama_pull(self, model_name):
        """Pull a model from Ollama, returning success as a boolean."""
        logger.info("Ollama model not installed. Executing 'ollama pull %s'...", model_name)
        try:
            result = subprocess.run(
                ["ollama", "pull", model_name], check=False, timeout=3600
            )
            return result.returncode == 0
        except (FileNotFoundError, OSError):
            logger.warning("Ollama executable not found. Skipping pull for %s.", model_name)
            return False
        except subprocess.TimeoutExpired:
            logger.warning("Ollama pull timed out for %s.", model_name)
            return False

    # ------------------------------------------------------------------
    # -- Cloud helper --------------------------------------------------
    # ------------------------------------------------------------------

    @functools.lru_cache(maxsize=512)
    def _cloud_key_for(self, model_name):
        """Return the environment variable name holding the API key for a cloud model."""
        lowered = (model_name or "").lower()
        for prefix, key_name in self.CLOUD_KEY_MAP.items():
            if lowered.startswith(prefix):
                return key_name
        return None

    # ------------------------------------------------------------------
    # -- Availability checks -------------------------------------------
    # ------------------------------------------------------------------

    def check_available(self, model_name):
        """Non-mutating availability check used by --check-only.

        Args:
            model_name (str): The model identifier to check.

        Returns:
            bool: True if the model is already usable without provisioning.
        """
        protocol = self.detect_protocol(model_name)
        if protocol == "cloud":
            key_name = self._cloud_key_for(model_name)
            return bool(key_name and os.getenv(key_name, ""))
        if protocol == "ollama":
            return self._ollama_has_model(model_name)
        # -- HuggingFace: only local copies are reported for check-only -------
        return self.resolve_local_model_path(model_name) is not None

    # ------------------------------------------------------------------
    # -- Provisioning entry point --------------------------------------
    # ------------------------------------------------------------------

    def ensure_model_available(self, model_name, silent=False):
        """Guarantee a model is available, provisioning it if necessary.

        Protocol dispatch with self-healing fallback. Never raises on network
        or disk failures; reports failures via the logger and returns False.

        Args:
            model_name (str): The model identifier to provision.
            silent (bool): When True, suppress informational console logging.

        Returns:
            bool: True when the model is available, False otherwise.
        """
        protocol = self.detect_protocol(model_name)
        if protocol == "cloud":
            return self._ensure_cloud(model_name)
        if protocol == "ollama":
            return self._ensure_ollama(model_name)
        return self._ensure_huggingface(model_name)

    def _ensure_cloud(self, model_name):
        """Validate that the corresponding cloud API key is active."""
        key_name = self._cloud_key_for(model_name)
        key = os.getenv(key_name or "", "")
        if key:
            logger.info("Cloud model %s is available (key %s configured).", model_name, key_name)
            return True
        logger.warning("Cloud model %s requires API key %s. Not available.", model_name, key_name)
        return False

    def _ensure_ollama(self, model_name):
        """Check `ollama list` and pull the model if it is absent."""
        if self._ollama_has_model(model_name):
            logger.info("Ollama model %s is already installed.", model_name)
            return True
        return self._ollama_pull(model_name)

    def _ensure_huggingface(self, model_name):
        """Resolve a local copy or download from HuggingFace Hub."""
        local_path = self.resolve_local_model_path(model_name)
        if local_path:
            logger.info("HuggingFace model %s resolved locally at %s.", model_name, local_path)
            return True

        if not HUGGINGFACE_HUB_AVAILABLE:
            logger.warning(
                "huggingface_hub is not installed. Cannot provision %s.", model_name
            )
            return False

        local_dir = self.models_dir / self._sanitize(model_name)
        logger.info("Downloading %s from HuggingFace Hub to %s...", model_name, local_dir)
        try:
            _hf_snapshot_download(
                repo_id=model_name,
                local_dir=str(local_dir),
                local_dir_use_symlinks=False,
            )
            logger.info("HuggingFace model %s provisioned successfully.", model_name)
            return True
        except Exception as exc:
            logger.warning(
                "[WARNING] Auto-provisioning failed for %s. Reverting to baseline model. (%s)",
                model_name,
                exc,
            )
            return False


# ----------------------------------------------------------------------
# -- Command-line interface --------------------------------------------
# ----------------------------------------------------------------------

def _report(model_name, protocol, available):
    """Print a single-line formal status report for the CLI."""
    state = "AVAILABLE" if available else "NOT AVAILABLE"
    print(f"[{state}] {model_name} (protocol={protocol})")


def main(argv=None):
    """CLI entry point for standalone provisioning.

    With no --model argument, provisions the default fast edge and heavy
    reasoning models. Use --check-only for a non-mutating availability audit.

    Args:
        argv (list[str] | None): Command-line arguments (defaults to sys.argv).

    Returns:
        int: Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Universal Dynamic Model Provisioner for TALOS."
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="Provision a specific model name. Defaults to the fast edge and heavy models.",
    )
    parser.add_argument(
        "--check-only", action="store_true",
        help="Report availability without downloading anything.",
    )
    args = parser.parse_args(argv)

    provisioner = ModelProvisioner()
    if args.model:
        models = [args.model]
    else:
        models = [m for m in (FAST_EDGE_MODEL, HEAVY_REASONING_MODEL) if m]

    exit_code = 0
    for model_name in models:
        protocol = provisioner.detect_protocol(model_name)
        if args.check_only:
            available = provisioner.check_available(model_name)
        else:
            available = provisioner.ensure_model_available(model_name)
        _report(model_name, protocol, available)
        if not available and not args.check_only:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())