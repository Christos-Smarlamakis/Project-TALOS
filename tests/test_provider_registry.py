# -*- coding: utf-8 -*-
"""
Module: test_provider_registry.py
Project: TALOS v5.18.1
Description:
    Unit tests for the pluggable ProviderRegistry and ProviderDescriptor
    value object (v5.16.2). Verifies the Open-Closed Principle contract:
    the canonical ten-provider catalogue is pre-registered, arbitrary new
    descriptors can be registered and retrieved without modifying core
    routing code, and ``is_active`` is evaluated dynamically from key
    presence (cloud) or port responsiveness (local Ollama). All tests are
    hermetic -- no live cloud endpoint is contacted.

Dependencies:
    - pytest: Test framework.
    - unittest.mock: Patching environment variables.
"""

import os
from unittest.mock import patch

from src.core.provider_registry import (
    ProviderRegistry,
    ProviderDescriptor,
    get_provider_registry,
)


class TestProviderRegistryDefaults:
    """Verify the canonical ten-provider catalogue is pre-registered."""

    def test_defaults_pre_registered(self):
        registry = ProviderRegistry()
        names = {d.name for d in registry.list_all()}
        expected = {
            "ollama", "nvidia", "deepseek", "gemini", "groq", "cerebras",
            "mistral", "huggingface", "openrouter", "anthropic",
        }
        assert names == expected

    def test_ollama_is_keyless_local_provider(self):
        registry = ProviderRegistry()
        ollama = registry.get("ollama")
        assert ollama is not None
        assert ollama.api_key_env is None
        assert ollama.category == "local_gpu"
        assert ollama.is_openai_compatible is True

    def test_gemini_is_non_openai_compatible(self):
        registry = ProviderRegistry()
        gemini = registry.get("gemini")
        assert gemini is not None
        assert gemini.is_openai_compatible is False


class TestProviderRegistryApi:
    """Verify register / get / list_all / list_active semantics."""

    def test_register_and_get(self):
        registry = ProviderRegistry()
        descriptor = ProviderDescriptor(
            name="custom_nim",
            base_url="https://nim.example.com/v1",
            api_key_env="CUSTOM_NIM_KEY",
            default_model="custom-model",
            category="cloud_heavy",
            is_openai_compatible=True,
        )
        registry.register(descriptor)
        got = registry.get("custom_nim")
        assert got is not None
        assert got.name == "custom_nim"
        assert got.default_model == "custom-model"
        assert got.base_url == "https://nim.example.com/v1"

    def test_register_overwrites_existing(self):
        registry = ProviderRegistry()
        registry.register(ProviderDescriptor(
            name="groq", base_url="https://override.example.com/v1",
            api_key_env="GROQ_API_KEY", default_model="custom",
        ))
        assert registry.get("groq").base_url == "https://override.example.com/v1"

    def test_get_unknown_returns_none(self):
        registry = ProviderRegistry()
        assert registry.get("does_not_exist") is None

    def test_list_active_reflects_key_presence(self):
        registry = ProviderRegistry()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}, clear=False):
            active = {d.name for d in registry.list_active()}
            assert "deepseek" in active
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}, clear=False):
            active = {d.name for d in registry.list_active()}
            assert "deepseek" not in active

    def test_singleton_is_shared(self):
        first = get_provider_registry()
        second = get_provider_registry()
        assert first is second


class TestAIManagerRegistryWiring:
    """Verify AIManager consumes the registry without regressions."""

    def test_aimanager_exposes_registry(self):
        from src.core.ai_manager import AIManager
        env = {
            "GEMINI_API_KEY": "", "NVIDIA_API_KEY": "", "GROQ_API_KEY": "",
            "CEREBRAS_API_KEY": "", "GITHUB_TOKEN": "", "MISTRAL_API_KEY": "",
            "OPENROUTER_API_KEY": "", "DEEPSEEK_API_KEY": "", "HF_TOKEN": "",
            "TALOS_USE_LOCAL": "1",
        }
        with patch.dict(os.environ, env, clear=False):
            with patch("src.core.ai_manager._try_import_openai", return_value=True), \
                 patch("src.core.ai_manager._try_import_genai", return_value=False), \
                 patch("src.core.ai_manager._GENAI_V2", False), \
                 patch("src.core.ai_manager._openai"), \
                 patch.object(AIManager, "_ensure_local_model", return_value=None):
                mgr = AIManager({"ai_provider_priority": ["local"], "failure_threshold": 5})
                assert mgr.provider_registry is not None
                assert isinstance(mgr.list_active_providers(), list)
                assert mgr.get_provider_descriptor("ollama") is not None
                assert mgr.get_provider_descriptor("unknown_provider") is None
