# -*- coding: utf-8 -*-
"""
Module: test_provider_registry.py
Project: TALOS v5.20.0
Description:
    Unit tests for the pluggable ProviderRegistry and ProviderDescriptor
    value object (v5.16.2, expanded v5.20.0). Verifies the Open-Closed
    Principle contract: the canonical sixteen-provider catalogue is
    pre-registered, arbitrary new descriptors can be registered and retrieved
    without modifying core routing code, the six v5.20.0 inference engines
    (SambaNova, Together, Fireworks, DeepInfra, Cohere, Perplexity) are
    reported active/inactive strictly from key presence, and
    ``get_available_providers()`` never raises. All tests are hermetic -- no
    live cloud endpoint is contacted.

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
    get_available_providers,
)


class TestProviderRegistryDefaults:
    """Verify the canonical sixteen-provider catalogue is pre-registered."""

    def test_defaults_pre_registered(self):
        registry = ProviderRegistry()
        names = {d.name for d in registry.list_all()}
        expected = {
            "ollama", "nvidia", "deepseek", "gemini", "groq", "cerebras",
            "mistral", "huggingface", "openrouter", "anthropic",
            "sambanova", "together", "fireworks", "deepinfra",
            "cohere", "perplexity",
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


class TestV520ProviderExpansion:
    """Verify the six v5.20.0 inference engines register with graceful key handling."""

    V520_NAMES = {
        "sambanova", "together", "fireworks", "deepinfra", "cohere", "perplexity",
    }
    V520_KEYS = (
        "SAMBANOVA_API_KEY", "TOGETHER_API_KEY", "FIREWORKS_API_KEY",
        "DEEPINFRA_API_KEY", "COHERE_API_KEY", "PERPLEXITY_API_KEY",
    )

    def test_new_providers_are_registered(self):
        registry = ProviderRegistry()
        names = {d.name for d in registry.list_all()}
        assert self.V520_NAMES <= names

    def test_new_providers_inactive_without_keys(self):
        env = {k: "" for k in self.V520_KEYS}
        with patch.dict(os.environ, env, clear=False):
            registry = ProviderRegistry()
            active = {d.name for d in registry.list_active()}
            assert self.V520_NAMES.isdisjoint(active)

    def test_new_providers_active_with_keys(self):
        env = {k: "test-key" for k in self.V520_KEYS}
        with patch.dict(os.environ, env, clear=False):
            registry = ProviderRegistry()
            active = {d.name for d in registry.list_active()}
            assert self.V520_NAMES <= active

    def test_get_available_providers_never_raises(self):
        env = {k: "" for k in self.V520_KEYS}
        with patch.dict(os.environ, env, clear=False):
            result = get_available_providers()
            assert isinstance(result, list)

    def test_llm_provider_enum_has_sixteen_members(self):
        from src.core.provider_registry import LLMProvider
        assert len(list(LLMProvider)) == 16


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
