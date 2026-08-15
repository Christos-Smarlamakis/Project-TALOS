# -*- coding: utf-8 -*-
"""
Module: test_model_provisioner.py
Project: TALOS v5.10.5
Description:
    Hermetic unit tests for the Universal Dynamic Model Provisioner
    (src/utils/model_provisioner.py). Covers protocol detection, the three-tier
    local path resolution cascade, mocked HuggingFace Hub and Ollama
    provisioning, and the self-healing fallback behavior.

    Key design decisions:
    - All network, subprocess, and filesystem side effects are mocked.
    - Tests never invoke a real download or the real Ollama daemon.
    - A temporary directory fixture isolates the in-tree models/ resolution.

Dependencies:
    - pytest: Test framework for fixture-based testing.
    - unittest.mock: Patching environment variables and module internals.
    - pathlib.Path: Temporary directory construction.
"""
import os
import sys
import pytest

from pathlib import Path
from unittest.mock import patch

# -- Ensure the project root is importable for src.* imports ------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.utils.model_provisioner as mp
from src.utils.model_provisioner import ModelProvisioner


# ----------------------------------------------------------------------
# -- Protocol detection tests ------------------------------------------
# ----------------------------------------------------------------------

class TestDetectProtocol:
    """Tests for ModelProvisioner.detect_protocol."""

    def test_ollama_colon(self):
        assert ModelProvisioner().detect_protocol("qwen2.5:14b") == "ollama"

    def test_ollama_colon_other(self):
        assert ModelProvisioner().detect_protocol("phi4:14b") == "ollama"

    def test_huggingface_slash(self):
        assert ModelProvisioner().detect_protocol("fermionresearch/Neutrino-8B") == "huggingface"

    def test_huggingface_slash_other(self):
        assert ModelProvisioner().detect_protocol("Qwen/Qwen2.5-7B-Instruct") == "huggingface"

    def test_cloud_gemini_prefix(self):
        assert ModelProvisioner().detect_protocol("gemini-2.5-flash") == "cloud"

    def test_cloud_nvidia_slash_prefix(self):
        assert ModelProvisioner().detect_protocol("nvidia/llama-3.1-nemotron") == "cloud"

    def test_cloud_groq_colon_prefix(self):
        assert ModelProvisioner().detect_protocol("groq:llama-3.3-70b") == "cloud"

    def test_default_untagged_is_ollama(self):
        assert ModelProvisioner().detect_protocol("nomic-embed-text") == "ollama"


# ----------------------------------------------------------------------
# -- Local path resolution tests ---------------------------------------
# ----------------------------------------------------------------------

class TestResolveLocalModelPath:
    """Tests for the three-tier local path resolution cascade."""

    def test_fast_edge_model_path_priority(self, tmp_path, monkeypatch):
        monkeypatch.setenv("FAST_EDGE_MODEL_PATH", str(tmp_path))
        p = ModelProvisioner(models_dir=tmp_path / "models")
        assert p.resolve_local_model_path("qwen2.5:14b") == str(tmp_path)

    def test_models_dir_priority_two(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FAST_EDGE_MODEL_PATH", raising=False)
        p = ModelProvisioner(models_dir=tmp_path / "models")
        local_dir = p.models_dir / p._sanitize("Qwen/Qwen2.5-7B-Instruct")
        local_dir.mkdir(parents=True)
        (local_dir / "config.json").write_text("{}")
        assert p.resolve_local_model_path("Qwen/Qwen2.5-7B-Instruct") == str(local_dir)

    def test_none_when_absent(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FAST_EDGE_MODEL_PATH", raising=False)
        p = ModelProvisioner(models_dir=tmp_path / "models")
        assert p.resolve_local_model_path("Qwen/Qwen2.5-7B-Instruct") is None


# ----------------------------------------------------------------------
# -- Provisioning tests (mocked) ---------------------------------------
# ----------------------------------------------------------------------

class TestEnsureModelAvailable:
    """Tests for ensure_model_available across all three protocols."""

    def test_ollama_already_installed(self):
        p = ModelProvisioner()
        with patch.object(p, "_ollama_has_model", return_value=True), \
             patch.object(p, "_ollama_pull") as mock_pull:
            assert p.ensure_model_available("qwen2.5:14b") is True
            mock_pull.assert_not_called()

    def test_ollama_pull_when_missing(self):
        p = ModelProvisioner()
        with patch.object(p, "_ollama_has_model", return_value=False), \
             patch.object(p, "_ollama_pull", return_value=True):
            assert p.ensure_model_available("qwen2.5:14b") is True

    def test_ollama_pull_failure_returns_false(self):
        p = ModelProvisioner()
        with patch.object(p, "_ollama_has_model", return_value=False), \
             patch.object(p, "_ollama_pull", return_value=False):
            assert p.ensure_model_available("qwen2.5:14b") is False

    def test_huggingface_download(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FAST_EDGE_MODEL_PATH", raising=False)
        p = ModelProvisioner(models_dir=tmp_path / "models")
        with patch.object(mp, "HUGGINGFACE_HUB_AVAILABLE", True), \
             patch.object(mp, "_hf_snapshot_download") as mock_dl:
            assert p.ensure_model_available("Qwen/Qwen2.5-7B-Instruct") is True
            mock_dl.assert_called_once()
            assert mock_dl.call_args.kwargs["repo_id"] == "Qwen/Qwen2.5-7B-Instruct"
            assert mock_dl.call_args.kwargs["local_dir_use_symlinks"] is False

    def test_huggingface_fallback_on_error(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FAST_EDGE_MODEL_PATH", raising=False)
        p = ModelProvisioner(models_dir=tmp_path / "models")
        with patch.object(mp, "HUGGINGFACE_HUB_AVAILABLE", True), \
             patch.object(mp, "_hf_snapshot_download", side_effect=RuntimeError("network down")):
            assert p.ensure_model_available("Qwen/Qwen2.5-7B-Instruct") is False

    def test_huggingface_resolves_local_before_download(self, tmp_path, monkeypatch):
        monkeypatch.delenv("FAST_EDGE_MODEL_PATH", raising=False)
        p = ModelProvisioner(models_dir=tmp_path / "models")
        local_dir = p.models_dir / p._sanitize("Qwen/Qwen2.5-7B-Instruct")
        local_dir.mkdir(parents=True)
        (local_dir / "config.json").write_text("{}")
        with patch.object(mp, "_hf_snapshot_download") as mock_dl:
            assert p.ensure_model_available("Qwen/Qwen2.5-7B-Instruct") is True
            mock_dl.assert_not_called()

    def test_cloud_with_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        assert ModelProvisioner().ensure_model_available("gemini-2.5-flash") is True

    def test_cloud_without_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        assert ModelProvisioner().ensure_model_available("gemini-2.5-flash") is False


# ----------------------------------------------------------------------
# -- Non-mutating availability check tests -----------------------------
# ----------------------------------------------------------------------

class TestCheckAvailable:
    """Tests for the check_available non-mutating audit path."""

    def test_check_available_ollama_installed(self):
        p = ModelProvisioner()
        with patch.object(p, "_ollama_has_model", return_value=True):
            assert p.check_available("qwen2.5:14b") is True

    def test_check_available_cloud_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "k")
        assert ModelProvisioner().check_available("gemini-2.5-pro") is True

    def test_check_available_cloud_no_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        assert ModelProvisioner().check_available("gemini-2.5-pro") is False


# ----------------------------------------------------------------------
# -- Ollama subprocess timeout (self-healing robustness) ---------------
# ----------------------------------------------------------------------

class TestOllamaTimeouts:
    """Tests that an unreachable Ollama daemon degrades gracefully."""

    def test_ollama_list_timeout_returns_empty(self):
        import subprocess
        p = ModelProvisioner()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["ollama", "list"], 10)):
            assert p._ollama_list() == set()

    def test_ollama_pull_timeout_returns_false(self):
        import subprocess
        p = ModelProvisioner()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["ollama", "pull", "qwen2.5:14b"], 3600)):
            assert p._ollama_pull("qwen2.5:14b") is False

