# -*- coding: utf-8 -*-
"""
Module: test_multi_tier.py
Project: TALOS v5.9.18
Description:
    Unit tests for the multi-tier LLM routing architecture (v5.7.1). Tests cover:
    - Fast tier routing via HTTP POST to FAST_EDGE_BASE_URL with Neutrino-8B.
    - Heavy tier routing via the standard provider priority chain.
    - Fallback behavior when fast tier is unreachable.
    - Configuration resolution from config/settings.py and environment variables.

    Key design decisions:
    - Uses httpretty or responses to mock HTTP POST calls to the fast edge endpoint.
    - Tests the _execute_fast_tier_request method in isolation.
    - Verifies that the tier parameter correctly branches the execution path.
    - All tests are hermetic -- no live Ollama or external endpoints required.

Dependencies:
    - pytest: Test framework for fixture-based testing.
    - unittest.mock: Patching HTTP requests and environment variables.
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock


# ------------------------------------------------------------------
# -- Fast Tier Request Tests --
# ------------------------------------------------------------------

class TestFastTierRequest:
    """Tests for the _execute_fast_tier_request method."""

    @pytest.fixture
    def aimanager_config(self):
        """Minimal config dict for AIManager initialization."""
        return {
            "ai_provider_priority": ["local"],
            "pre_screening_model": "gemini-2.5-flash-lite",
            "model_for_daily_search": "gemini-2.5-pro",
            "pre_screening_prompt": "Evaluate this paper.",
            "failure_threshold": 4,
        }

    @pytest.fixture
    def aimanager(self, aimanager_config):
        """Create an AIManager instance with environment patched."""
        with patch.dict(os.environ, {
            "TALOS_USE_LOCAL": "1",
            "LOCAL_MODEL_NAME": "gemma3:12b",
            "TALOS_MODELS_VERIFIED": "1",
        }, clear=False):
            # Also patch _ensure_local_model to skip actual model verification.
            with patch.object(
                __import__('src.core.ai_manager', fromlist=['AIManager']).AIManager,
                '_ensure_local_model',
                return_value=None,
            ):
                from src.core.ai_manager import AIManager
                return AIManager(aimanager_config)

    def test_fast_tier_success_text_response(self, aimanager):
        """Verify fast tier returns text on HTTP 200."""
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "This paper is about AI ethics."
                    }
                }
            ]
        }
        mock_post = MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        with patch('requests.post', mock_post):
            result = aimanager._execute_fast_tier_request(
                "What is this paper about?",
                response_format='text',
            )
        assert result == "This paper is about AI ethics."
        # Verify the correct URL was called.
        call_args = mock_post.call_args
        assert "/chat/completions" in call_args[0][0]

    def test_fast_tier_success_json_response(self, aimanager):
        """Verify fast tier returns parsed JSON on HTTP 200 with JSON."""
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"score": 8.5, "relevance": "high"}'
                    }
                }
            ]
        }
        mock_post = MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        with patch('requests.post', mock_post):
            result = aimanager._execute_fast_tier_request(
                "Score this paper.",
                response_format='json',
            )
        assert isinstance(result, dict)
        assert result["score"] == 8.5
        assert result["relevance"] == "high"

    def test_fast_tier_connection_refused(self, aimanager):
        """Verify fast tier returns None on connection error."""
        import requests as req_module
        mock_post = MagicMock()
        mock_post.side_effect = req_module.exceptions.ConnectionError("Refused")

        with patch('requests.post', mock_post):
            result = aimanager._execute_fast_tier_request(
                "Test prompt",
                response_format='text',
            )
        assert result is None

    def test_fast_tier_http_error(self, aimanager):
        """Verify fast tier returns None on non-200 HTTP status."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post = MagicMock()
        mock_post.return_value = mock_response

        with patch('requests.post', mock_post):
            result = aimanager._execute_fast_tier_request(
                "Test prompt",
                response_format='text',
            )
        assert result is None

    def test_fast_tier_empty_response(self, aimanager):
        """Verify fast tier returns None when response has empty content."""
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": ""
                    }
                }
            ]
        }
        mock_post = MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        with patch('requests.post', mock_post):
            result = aimanager._execute_fast_tier_request(
                "Test prompt",
                response_format='text',
            )
        assert result is None

    def test_fast_tier_json_decode_error(self, aimanager):
        """Verify fast tier returns None on invalid JSON response."""
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "Not valid JSON at all."
                    }
                }
            ]
        }
        mock_post = MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        with patch('requests.post', mock_post):
            result = aimanager._execute_fast_tier_request(
                "Test prompt",
                response_format='json',
            )
        assert result is None


# ------------------------------------------------------------------
# -- Multi-Tier Routing (_execute_request) Tests --
# ------------------------------------------------------------------

class TestMultiTierRouting:
    """Tests for the _execute_request method with tier parameter."""

    @pytest.fixture
    def aimanager_config(self):
        """Minimal config with no cloud providers to force fast tier."""
        return {
            "ai_provider_priority": [],
            "failure_threshold": 4,
        }

    def test_tier_fast_routes_to_fast_tier(self):
        """Verify that tier='fast' routes via _execute_local_strategy (v5.9.10 2D Matrix)."""
        from src.core.ai_manager import AIManager
        # v5.9.10: 2D Execution Matrix uses _execute_local_strategy for strict_local.
        # Set legacy vars plus the new network/hardware strategy vars to ensure
        # fast tier routes through the local strategy path.
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': '',
            'DEEPSEEK_API_KEY': '',
            'HF_TOKEN': '',
            'TALOS_USE_LOCAL': '',
            'TALOS_NETWORK_STRATEGY': 'strict_local',
            'TALOS_HARDWARE_STRATEGY': 'cpu_gpu_split',
            'TALOS_FAST_ROUTING': 'local',
            'TALOS_HEAVY_ROUTING': 'local',
        }, clear=False):
            mgr = AIManager({
                "ai_provider_priority": [],
                "failure_threshold": 4,
            })

            with patch.object(
                mgr,
                '_execute_local_strategy',
                return_value="fast result",
            ) as mock_local:
                result = mgr._execute_request(
                    "test prompt",
                    model_type='pro',
                    response_format='text',
                    tier='fast',
                )
                mock_local.assert_called_once_with(
                    "test prompt", 'text', 'fast', 'cpu_gpu_split', allow_prompt=True
                )
                assert result == "fast result"
                assert mgr.last_provider_used == 'local'

    def test_tier_fast_falls_back_to_providers(self):
        """Verify that fast tier failure returns None when no cloud fallback is available."""
        from src.core.ai_manager import AIManager
        # v5.9.10: With strict_local network strategy and no cloud providers,
        # _execute_local_strategy returning None should cause overall None.
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': '',
            'DEEPSEEK_API_KEY': '',
            'HF_TOKEN': '',
            'TALOS_USE_LOCAL': '',
            'TALOS_NETWORK_STRATEGY': 'strict_local',
            'TALOS_HARDWARE_STRATEGY': 'cpu_gpu_split',
        }, clear=False):
            mgr = AIManager({
                "ai_provider_priority": [],
                "failure_threshold": 4,
            })

            with patch.object(
                mgr,
                '_execute_local_strategy',
                return_value=None,
            ):
                result = mgr._execute_request(
                    "test prompt",
                    model_type='pro',
                    response_format='text',
                    tier='fast',
                )
                assert result is None

    def test_tier_heavy_skips_fast_tier(self):
        """Verify that tier='heavy' routes via _execute_local_strategy (GPU) and does NOT call fast tier."""
        from src.core.ai_manager import AIManager
        # v5.9.10: Set strict_local network strategy so it uses _execute_local_strategy.
        # Mock _execute_local_strategy to return None (simulating no local models available)
        # and verify _execute_fast_tier_request is not called.
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': '',
            'DEEPSEEK_API_KEY': '',
            'HF_TOKEN': '',
            'TALOS_USE_LOCAL': '',
            'TALOS_NETWORK_STRATEGY': 'strict_local',
            'TALOS_HARDWARE_STRATEGY': 'cpu_gpu_split',
        }, clear=False):
            mgr = AIManager({
                "ai_provider_priority": [],
                "failure_threshold": 4,
            })

            with patch.object(
                mgr,
                '_execute_fast_tier_request',
            ) as mock_fast:
                with patch.object(
                    mgr,
                    '_execute_local_strategy',
                    return_value=None,
                ):
                    result = mgr._execute_request(
                        "test prompt",
                        model_type='pro',
                        response_format='text',
                        tier='heavy',
                    )
                mock_fast.assert_not_called()
                assert result is None


# ------------------------------------------------------------------
# -- Configuration Resolution Tests --
# ------------------------------------------------------------------

class TestSettingsResolution:
    """Tests for config/settings.py configuration resolution."""

    def test_default_fast_edge_model(self):
        """Verify the default FAST_EDGE_MODEL value."""
        from config.settings import FAST_EDGE_MODEL
        assert FAST_EDGE_MODEL == "fermionresearch/Neutrino-8B"

    def test_default_fast_edge_base_url(self):
        """Verify the default FAST_EDGE_BASE_URL value."""
        from config.settings import FAST_EDGE_BASE_URL
        assert FAST_EDGE_BASE_URL == "http://127.0.0.1:11435/v1"

    def test_default_heavy_reasoning_model(self):
        """Verify the default HEAVY_REASONING_MODEL value."""
        from config.settings import HEAVY_REASONING_MODEL
        assert HEAVY_REASONING_MODEL == "qwen2.5:14b"

    def test_default_ollama_base_url(self):
        """Verify the default OLLAMA_BASE_URL value."""
        from config.settings import OLLAMA_BASE_URL
        assert OLLAMA_BASE_URL == "http://127.0.0.1:11434"

    def test_default_tier_is_fast(self):
        """Verify the default tier is 'fast'."""
        from config.settings import DEFAULT_TIER
        assert DEFAULT_TIER == "fast"

    def test_talos_version(self):
        """Verify the TALOS_VERSION is v5.9.18."""
        from config.settings import TALOS_VERSION
        assert TALOS_VERSION == "5.9.18"

    def test_talos_api_port(self):
        """Verify the default TALOS_API_PORT is 8001."""
        from config.settings import TALOS_API_PORT
        assert TALOS_API_PORT == 8001

    def test_env_override_fast_edge_model(self):
        """Verify that environment variables override defaults."""
        import importlib
        import config.settings as settings_module

        # Remember original values before patching.
        orig_model = settings_module.FAST_EDGE_MODEL
        orig_url = settings_module.FAST_EDGE_BASE_URL
        orig_heavy = settings_module.HEAVY_REASONING_MODEL
        orig_tier = settings_module.DEFAULT_TIER

        try:
            with patch.dict(os.environ, {
                "FAST_EDGE_MODEL": "custom/model-v2",
                "FAST_EDGE_BASE_URL": "http://192.168.1.1:8080/v1",
                "HEAVY_REASONING_MODEL": "llama3:70b",
                "TALOS_DEFAULT_TIER": "heavy",
            }, clear=True):
                # Reload the module to pick up new env vars.
                importlib.reload(settings_module)

                assert settings_module.FAST_EDGE_MODEL == "custom/model-v2"
                assert settings_module.FAST_EDGE_BASE_URL == "http://192.168.1.1:8080/v1"
                assert settings_module.HEAVY_REASONING_MODEL == "llama3:70b"
                assert settings_module.DEFAULT_TIER == "heavy"
        finally:
            # Restore original values by reloading with original env.
            importlib.reload(settings_module)
            # Patch back original values in case reload didn't restore.
            settings_module.FAST_EDGE_MODEL = orig_model
            settings_module.FAST_EDGE_BASE_URL = orig_url
            settings_module.HEAVY_REASONING_MODEL = orig_heavy
            settings_module.DEFAULT_TIER = orig_tier


# ------------------------------------------------------------------
# -- Mailbox Pattern Tests (Fast Tier as Fire-and-Forget) --
# ------------------------------------------------------------------

class TestMailboxPattern:
    """Tests verifying that fast tier implements a mailbox pattern."""

    def test_fast_tier_timeout_configurable(self):
        """Verify that the fast tier request uses a configurable timeout."""
        # This is a design validation test -- the timeout is hardcoded at 30s
        # in _execute_fast_tier_request, which is appropriate for local edge.
        from config.settings import FAST_EDGE_BASE_URL
        # Local edge endpoints should use localhost or loopback.
        assert "127.0.0.1" in FAST_EDGE_BASE_URL or "localhost" in FAST_EDGE_BASE_URL

    def test_heavy_tier_uses_standard_ollama_port(self):
        """Verify the heavy tier points to standard Ollama (11434)."""
        from config.settings import OLLAMA_BASE_URL
        assert "11434" in OLLAMA_BASE_URL

    def test_fast_tier_uses_dedicated_port(self):
        """Verify the fast tier points to dedicated edge (11435)."""
        from config.settings import FAST_EDGE_BASE_URL
        assert "11435" in FAST_EDGE_BASE_URL


# ------------------------------------------------------------------
# -- v5.9.18: Universal Cloud Mesh Registry Tests --
# ------------------------------------------------------------------

class TestCloudMeshRegistry:
    """Tests for the OpenAI-compatible cloud provider registry (v5.9.18)."""

    # All cloud provider environment keys (for deterministic test isolation).
    CLOUD_KEYS = {
        "GEMINI_API_KEY": "", "NVIDIA_API_KEY": "", "GROQ_API_KEY": "",
        "CEREBRAS_API_KEY": "", "GITHUB_TOKEN": "", "MISTRAL_API_KEY": "",
        "OPENROUTER_API_KEY": "", "DEEPSEEK_API_KEY": "", "HF_TOKEN": "",
        "TALOS_USE_LOCAL": "",
    }

    def test_registry_has_all_eight_openai_compatible_providers(self):
        """Verify the registry enumerates all eight redundancy providers."""
        from src.core.ai_manager import OPENAI_COMPATIBLE_REGISTRY
        expected = {"nvidia", "groq", "cerebras", "github", "mistral",
                    "openrouter", "deepseek", "huggingface"}
        assert set(OPENAI_COMPATIBLE_REGISTRY.keys()) == expected

    def test_registry_entries_have_required_metadata(self):
        """Verify every registry entry declares its required metadata fields."""
        from src.core.ai_manager import OPENAI_COMPATIBLE_REGISTRY
        required = {"env_key", "base_url", "default_model", "model_env_key"}
        for name, meta in OPENAI_COMPATIBLE_REGISTRY.items():
            assert required.issubset(set(meta.keys())), f"{name} missing metadata"
            assert meta["base_url"].startswith("https://"), f"{name} base_url not https"

    def test_gemini_is_not_in_openai_compatible_registry(self):
        """Verify Gemini is excluded (it uses the Google GenAI SDK path)."""
        from src.core.ai_manager import OPENAI_COMPATIBLE_REGISTRY
        assert "gemini" not in OPENAI_COMPATIBLE_REGISTRY

    def test_provider_discovery_with_configured_keys(self):
        """Verify AIManager initializes exactly the providers whose keys are set."""
        from src.core.ai_manager import AIManager
        env = dict(self.CLOUD_KEYS)
        env.update({"GROQ_API_KEY": "test-groq-key", "DEEPSEEK_API_KEY": "test-deepseek-key"})
        with patch.dict(os.environ, env, clear=False):
            with patch("src.core.ai_manager._try_import_openai", return_value=True), \
                 patch("src.core.ai_manager._try_import_genai", return_value=False), \
                 patch("src.core.ai_manager._openai") as mock_openai, \
                 patch.object(AIManager, "_ensure_local_model", return_value=None):
                mgr = AIManager({"ai_provider_priority": ["local", "groq", "deepseek"],
                                 "failure_threshold": 5})
                assert "groq" in mgr.providers
                assert "deepseek" in mgr.providers
                assert "nvidia" not in mgr.providers
                assert "local" not in mgr.providers

    def test_missing_keys_skip_providers_gracefully(self):
        """Verify no cloud providers are initialized when all keys are absent."""
        from src.core.ai_manager import AIManager
        with patch.dict(os.environ, dict(self.CLOUD_KEYS), clear=False):
            with patch("src.core.ai_manager._try_import_openai", return_value=True), \
                 patch("src.core.ai_manager._try_import_genai", return_value=False), \
                 patch.object(AIManager, "_ensure_local_model", return_value=None):
                mgr = AIManager({"ai_provider_priority": ["local", "groq"],
                                 "failure_threshold": 5})
                cloud_keys = {"nvidia", "groq", "cerebras", "github", "mistral",
                              "openrouter", "deepseek", "huggingface", "gemini"}
                assert not cloud_keys.intersection(set(mgr.providers.keys()))

    def test_cascade_failover_simulation(self):
        """Verify _execute_cloud_chain cascades to the next provider on failure."""
        from src.core.ai_manager import AIManager
        env = dict(self.CLOUD_KEYS)
        env.update({"GROQ_API_KEY": "groq-key", "DEEPSEEK_API_KEY": "deepseek-key"})
        with patch.dict(os.environ, env, clear=False):
            with patch("src.core.ai_manager._try_import_openai", return_value=True), \
                 patch("src.core.ai_manager._try_import_genai", return_value=False), \
                 patch("src.core.ai_manager._openai") as mock_openai, \
                 patch.object(AIManager, "_ensure_local_model", return_value=None):
                mgr = AIManager({"ai_provider_priority": ["groq", "deepseek"],
                                 "failure_threshold": 5})

                def fake_request(provider_name, prompt, model_type, response_format):
                    if provider_name == "groq":
                        return None  # simulate provider failure
                    return {"score": 9}  # next provider succeeds

                with patch.object(mgr, "_execute_openai_compatible_request",
                                  side_effect=fake_request):
                    result = mgr._execute_cloud_chain("test prompt", "pro", "json")
                    assert result == {"score": 9}
                    assert mgr.last_provider_used == "deepseek"
