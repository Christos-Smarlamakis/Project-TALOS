# -*- coding: utf-8 -*-
"""
Module: test_model_manager.py
Project: TALOS v5.9.17
Description:
    Unit tests for the TUI model manager helper functions (model_manager.py).
    Tests cover: Ollama connectivity checks, quantization tag categorization,
    VRAM fitness labels, .env key updates, and execution mode configuration.
    All tests use unittest.mock to avoid real network/system calls.

Dependencies:
    - unittest: Test framework.
    - unittest.mock: Mocking for HTTP, subprocess, filesystem.
    - src.ai.llm.model_manager: The module under test.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# -- Ensure project root is importable --
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


class TestCheckOllamaAlive(unittest.TestCase):
    """Tests for check_ollama_alive() helper."""

    @patch("src.ai.llm.model_manager.requests.get")
    def test_returns_true_when_200(self, mock_get):
        """check_ollama_alive should return True when /api/tags returns 200."""
        from src.ai.llm.model_manager import check_ollama_alive
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = check_ollama_alive()
        self.assertTrue(result)

    @patch("src.ai.llm.model_manager.requests.get")
    def test_returns_false_when_not_200(self, mock_get):
        """check_ollama_alive should return False when /api/tags returns 500."""
        from src.ai.llm.model_manager import check_ollama_alive
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = check_ollama_alive()
        self.assertFalse(result)

    @patch("src.ai.llm.model_manager.requests.get")
    def test_returns_false_on_connection_error(self, mock_get):
        """check_ollama_alive should return False when requests raises an exception."""
        from src.ai.llm.model_manager import check_ollama_alive
        mock_get.side_effect = ConnectionError("No route to host")

        result = check_ollama_alive()
        self.assertFalse(result)


class TestCategorizeTags(unittest.TestCase):
    """Tests for _categorize_tags() quantization grouping logic."""

    def setUp(self):
        from src.ai.llm.model_manager import _categorize_tags
        self._categorize_tags = _categorize_tags

    def test_q8_tag_goes_to_8bit(self):
        """Q8_0 tag should be placed in the '8-bit (Q8)' bucket."""
        tags = [{"tag": "q8_0", "size_gb": 10.0, "full_name": "qwen2.5:q8_0"}]
        result = self._categorize_tags(tags, "qwen2.5", [])
        self.assertIn("8-bit (Q8)", result)
        self.assertEqual(len(result["8-bit (Q8)"]), 1)
        self.assertEqual(result["8-bit (Q8)"][0]["tag"], "q8_0")

    def test_q4_k_m_tag_goes_to_4bit(self):
        """Q4_K_M tag should be placed in the '4-bit (Q4)' bucket."""
        tags = [{"tag": "q4_K_M", "size_gb": 5.0, "full_name": "qwen2.5:q4_K_M"}]
        result = self._categorize_tags(tags, "qwen2.5", [])
        self.assertIn("4-bit (Q4)", result)
        self.assertEqual(len(result["4-bit (Q4)"]), 1)

    def test_q5_tag_grouped_with_q4(self):
        """Q5_* tags should be grouped with 4-bit (Q4) bucket."""
        tags = [{"tag": "q5_K_M", "size_gb": 6.0, "full_name": "qwen2.5:q5_K_M"}]
        result = self._categorize_tags(tags, "qwen2.5", [])
        self.assertIn("4-bit (Q4)", result)
        self.assertEqual(result["4-bit (Q4)"][0]["tag"], "q5_K_M")

    def test_q2_k_tag_goes_to_2bit(self):
        """Q2_K tag should be placed in the '2-bit (Q2)' bucket."""
        tags = [{"tag": "q2_K", "size_gb": 3.0, "full_name": "qwen2.5:q2_K"}]
        result = self._categorize_tags(tags, "qwen2.5", [])
        self.assertIn("2-bit (Q2)", result)
        self.assertEqual(len(result["2-bit (Q2)"]), 1)

    def test_q1_0_tag_goes_to_1bit(self):
        """Q1_0 tag should be placed in the '1-bit (Q1)' bucket."""
        tags = [{"tag": "q1_0", "size_gb": 1.5, "full_name": "qwen2.5:q1_0"}]
        result = self._categorize_tags(tags, "qwen2.5", [])
        self.assertIn("1-bit (Q1)", result)
        self.assertEqual(len(result["1-bit (Q1)"]), 1)

    def test_unknown_tag_goes_to_other(self):
        """Unrecognized tag like 'latest' should go to 'Other / No tag'."""
        tags = [{"tag": "latest", "size_gb": 8.0, "full_name": "gemma3:latest"}]
        result = self._categorize_tags(tags, "gemma3", [])
        self.assertIn("Other / No tag", result)
        self.assertEqual(len(result["Other / No tag"]), 1)

    def test_marks_installed_correctly(self):
        """Tags whose full_name is in the installed list should have installed=True."""
        tags = [{"tag": "q8_0", "size_gb": 10.0, "full_name": "qwen2.5:q8_0"}]
        installed = ["qwen2.5:q8_0", "qwen2.5:q4_K_M"]
        result = self._categorize_tags(tags, "qwen2.5", installed)
        self.assertTrue(result["8-bit (Q8)"][0]["installed"])

    def test_marks_not_installed_correctly(self):
        """Tags not in the installed list should have installed=False."""
        tags = [{"tag": "q8_0", "size_gb": 10.0, "full_name": "qwen2.5:q8_0"}]
        installed = ["qwen2.5:q4_K_M"]
        result = self._categorize_tags(tags, "qwen2.5", installed)
        self.assertFalse(result["8-bit (Q8)"][0]["installed"])

    def test_empty_categories_removed(self):
        """Empty categories should be removed from the returned dict."""
        tags = [{"tag": "q8_0", "size_gb": 10.0, "full_name": "qwen2.5:q8_0"}]
        result = self._categorize_tags(tags, "qwen2.5", [])
        # Only 8-bit should be present; all others removed
        self.assertEqual(len(result), 1)
        self.assertIn("8-bit (Q8)", result)
        self.assertNotIn("4-bit (Q4)", result)

    def test_multiple_tags_in_same_category(self):
        """Multiple tags belonging to the same bucket should all be included."""
        tags = [
            {"tag": "q8_0", "size_gb": 10.0, "full_name": "m:q8_0"},
            {"tag": "q_8", "size_gb": 9.0, "full_name": "m:q_8"},
            {"tag": "iq8", "size_gb": 8.5, "full_name": "m:iq8"},
        ]
        result = self._categorize_tags(tags, "m", [])
        self.assertEqual(len(result["8-bit (Q8)"]), 3)

    def test_empty_input_returns_empty(self):
        """Empty tags list should return an empty dict."""
        result = self._categorize_tags([], "qwen2.5", [])
        self.assertEqual(result, {})


class TestFitsLabel(unittest.TestCase):
    """Tests for _fits_label() VRAM fitness indicator."""

    def setUp(self):
        from src.ai.llm.model_manager import _fits_label
        self._fits_label = _fits_label

    def test_returns_empty_when_no_size(self):
        """Should return '' when size_gb is None/0."""
        self.assertEqual(self._fits_label(True, None, 10), "")
        self.assertEqual(self._fits_label(True, 0, 10), "")

    def test_returns_empty_when_no_vram_limit(self):
        """Should return '' when vram_limit is None/0."""
        self.assertEqual(self._fits_label(True, 5, None), "")
        self.assertEqual(self._fits_label(True, 5, 0), "")

    def test_fits_label_at_low_ratio(self):
        """Ratio <= 0.7 should return ' [FITS]'."""
        label = self._fits_label(True, 5, 10)  # ratio = 0.5
        self.assertEqual(label, " [FITS]")

    def test_tight_label_at_moderate_ratio(self):
        """Ratio between 0.7 and 1.0 should return ' [TIGHT]'."""
        label = self._fits_label(True, 8, 10)  # ratio = 0.8
        self.assertEqual(label, " [TIGHT]")

    def test_too_big_label_at_high_ratio(self):
        """Ratio > 1.0 should return ' [TOO BIG]'."""
        label = self._fits_label(True, 12, 10)  # ratio = 1.2
        self.assertEqual(label, " [TOO BIG]")

    def test_no_unicode_emojis_in_labels(self):
        """All labels must be pure ASCII text badges -- no Unicode symbols."""
        from src.ai.llm.model_manager import _fits_label
        for size in [3, 7, 12]:
            for limit in [10]:
                label = _fits_label(True, size, limit)
                # All characters should be printable ASCII or empty
                if label:
                    self.assertTrue(
                        all(ord(c) < 128 for c in label),
                        f"Non-ASCII character found in label: '{label}'"
                    )


class TestDotenvKeyUpdates(unittest.TestCase):
    """Tests for .env key setting behavior via dotenv.set_key."""

    @patch("src.ai.llm.model_manager.dotenv_values")
    @patch("src.ai.llm.model_manager._set_key")
    @patch("src.ai.llm.model_manager.questionary.select")
    @patch("src.ai.llm.model_manager.questionary.text")
    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_execution_mode_local_sets_backward_compat_keys(
        self, mock_confirm, mock_text, mock_select,
        mock_set_key, mock_dotenv_values
    ):
        """Setting execution mode to 'local' should set TALOS_USE_LOCAL=1 and TALOS_ALLOW_CLOUD_FALLBACK=0."""
        from src.ai.llm.model_manager import select_execution_mode

        mock_dotenv_values.return_value = {"TALOS_EXECUTION_MODE": "hybrid", "TALOS_FAST_ROUTING": "cloud", "TALOS_HEAVY_ROUTING": "cloud"}
        # v5.9.1: select returns new value "pure-local" via Choice(value=...)
        mock_select.return_value.ask.return_value = "pure-local"
        # v5.9.1: confirmation is a direct questionary.confirm call
        mock_confirm.return_value.ask.return_value = True

        with patch("os.system"), patch("builtins.input"):
            select_execution_mode("/fake/.env")

        # Check that all routing keys were set
        calls = {args[1] for args, _ in mock_set_key.call_args_list}
        self.assertIn("TALOS_EXECUTION_MODE", calls)
        self.assertIn("TALOS_FAST_ROUTING", calls)
        self.assertIn("TALOS_HEAVY_ROUTING", calls)
        self.assertIn("TALOS_USE_LOCAL", calls)
        self.assertIn("TALOS_ALLOW_CLOUD_FALLBACK", calls)

    @patch("src.ai.llm.model_manager.dotenv_values")
    @patch("src.ai.llm.model_manager._set_key")
    @patch("src.ai.llm.model_manager.questionary.select")
    @patch("src.ai.llm.model_manager.questionary.text")
    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_execution_mode_cancel_does_nothing(
        self, mock_confirm, mock_text, mock_select,
        mock_set_key, mock_dotenv_values
    ):
        """Cancelling execution mode selection should not call _set_key."""
        from src.ai.llm.model_manager import select_execution_mode

        mock_dotenv_values.return_value = {"TALOS_EXECUTION_MODE": "local"}
        mock_select.return_value.ask.return_value = None  # User cancelled

        with patch("os.system"), patch("builtins.input"):
            select_execution_mode("/fake/.env")

        mock_set_key.assert_not_called()

    @patch("src.ai.llm.model_manager.dotenv_values")
    @patch("src.ai.llm.model_manager._set_key")
    @patch("src.ai.llm.model_manager.questionary.select")
    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_cloud_models_skip_when_no_api_key(
        self, mock_confirm, mock_select, mock_set_key, mock_dotenv_values
    ):
        """When no GEMINI/DEEPSEEK/HF keys are present, cloud models should skip without error."""
        from src.ai.llm.model_manager import select_cloud_models

        mock_dotenv_values.return_value = {}
        mock_select.return_value.ask.return_value = "Cancel"
        mock_confirm.return_value.ask.return_value = False

        # Should run without exception
        with patch("os.system"), patch("builtins.input"):
            select_cloud_models("/fake/.env")

        # No keys should have been set since no API keys available
        mock_set_key.assert_not_called()


class TestPathResolution(unittest.TestCase):
    """Tests for path and .env resolution."""

    def test_env_path_is_absolute(self):
        """_ENV_PATH should be an absolute path ending in .env."""
        from src.ai.llm.model_manager import _ENV_PATH
        self.assertTrue(os.path.isabs(_ENV_PATH), f"Not absolute: {_ENV_PATH}")
        self.assertTrue(_ENV_PATH.endswith(".env"), f"Does not end with .env: {_ENV_PATH}")

    def test_project_root_is_absolute(self):
        """_PROJECT_ROOT should be an absolute path."""
        from src.ai.llm.model_manager import _PROJECT_ROOT
        self.assertTrue(_PROJECT_ROOT.is_absolute(), f"Not absolute: {_PROJECT_ROOT}")


class TestGetInstalledModels(unittest.TestCase):
    """Tests for get_installed_models()."""

    @patch("src.ai.llm.model_manager.requests.get")
    def test_returns_model_names_list(self, mock_get):
        """Should parse /api/tags JSON and return list of model names."""
        from src.ai.llm.model_manager import get_installed_models
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:14b"},
                {"name": "gemma3:12b"},
            ]
        }
        mock_get.return_value = mock_response

        result = get_installed_models()
        self.assertEqual(result, ["qwen2.5:14b", "gemma3:12b"])

    @patch("src.ai.llm.model_manager.requests.get")
    def test_returns_empty_on_failure(self, mock_get):
        """Should return [] when request raises an exception."""
        from src.ai.llm.model_manager import get_installed_models
        mock_get.side_effect = ConnectionError("Timeout")

        result = get_installed_models()
        self.assertEqual(result, [])


class TestGetAvailableTags(unittest.TestCase):
    """Tests for get_available_tags()."""

    @patch("src.ai.llm.model_manager.subprocess.run")
    def test_parses_tags_from_show_output(self, mock_run):
        """Should parse GB-sized tags from ollama show output."""
        from src.ai.llm.model_manager import get_available_tags

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "  Model\n"
            "    architecture        qwen2\n"
            "    parameters          14.8B\n"
            "  Tags:\n"
            "    q4_K_M                8.5 GB\n"
            "    q8_0                 14.5 GB\n"
            "  License\n"
            "    Apache 2.0\n"
        )
        mock_run.return_value = mock_result

        result = get_available_tags("qwen2.5")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["tag"], "q4_K_M")
        self.assertEqual(result[0]["full_name"], "qwen2.5:q4_K_M")
        self.assertAlmostEqual(result[0]["size_gb"], 8.5)
        self.assertEqual(result[1]["tag"], "q8_0")

    @patch("src.ai.llm.model_manager.subprocess.run")
    def test_returns_empty_on_command_failure(self, mock_run):
        """Should return [] when ollama show exits non-zero."""
        from src.ai.llm.model_manager import get_available_tags

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error: model not found"
        mock_run.return_value = mock_result

        result = get_available_tags("nonexistent")
        self.assertEqual(result, [])


class TestConfirmSettingChange(unittest.TestCase):
    """Tests for _confirm_setting_change() safety lock helper (v5.8.6)."""

    def setUp(self):
        from src.ai.llm.model_manager import _confirm_setting_change
        self._confirm_setting_change = _confirm_setting_change

    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_confirms_when_user_says_yes(self, mock_confirm):
        """When user confirms, _confirm_setting_change should return True."""
        mock_confirm.return_value.ask.return_value = True
        result = self._confirm_setting_change(
            "/fake/.env", "TEST_KEY", "old_value", "new_value"
        )
        self.assertTrue(result)

    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_rejects_when_user_says_no(self, mock_confirm):
        """When user declines, _confirm_setting_change should return False."""
        mock_confirm.return_value.ask.return_value = False
        result = self._confirm_setting_change(
            "/fake/.env", "TEST_KEY", "old_value", "new_value"
        )
        self.assertFalse(result)

    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_returns_false_when_user_cancels(self, mock_confirm):
        """When user cancels (None), _confirm_setting_change should return False."""
        mock_confirm.return_value.ask.return_value = None
        result = self._confirm_setting_change(
            "/fake/.env", "TEST_KEY", "old_value", "new_value"
        )
        self.assertFalse(result)

    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_displays_empty_old_value_as_empty(self, mock_confirm):
        """When old_value is empty/None, panel should show '(empty)' without crashing."""
        mock_confirm.return_value.ask.return_value = True
        # Should not raise; empty string displayed as "(empty)"
        result = self._confirm_setting_change(
            "/fake/.env", "LOCAL_EMBEDDING_MODEL", "", "nomic-embed-text"
        )
        self.assertTrue(result)


class TestSubMenuCancellation(unittest.TestCase):
    """Tests for sub-menu cancellation flows (v5.8.6)."""

    @patch("src.ai.llm.model_manager._set_key")
    @patch("src.ai.llm.model_manager.dotenv_values")
    @patch("src.ai.llm.model_manager.questionary.select")
    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_execution_mode_cancel_via_sentinel(
        self, mock_confirm, mock_select, mock_dotenv_values, mock_set_key
    ):
        """When user selects Cancel in execution mode, _set_key should not be called."""
        from src.ai.llm.model_manager import select_execution_mode

        mock_dotenv_values.return_value = {"TALOS_EXECUTION_MODE": "local"}
        mock_select.return_value.ask.return_value = "__cancel__"
        mock_confirm.return_value.ask.return_value = False

        with patch("os.system"), patch("builtins.input"):
            select_execution_mode("/fake/.env")

        mock_set_key.assert_not_called()

    @patch("src.ai.llm.model_manager._set_key")
    @patch("src.ai.llm.model_manager.dotenv_values")
    @patch("src.ai.llm.model_manager.questionary.select")
    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_execution_mode_confirm_then_apply(
        self, mock_confirm, mock_select, mock_dotenv_values, mock_set_key
    ):
        """When user selects a mode and confirms, _set_key should be called."""
        from src.ai.llm.model_manager import select_execution_mode

        mock_dotenv_values.return_value = {"TALOS_EXECUTION_MODE": "local"}
        # v5.9.1: use "pure-cloud" which maps to fast=cloud, heavy=cloud
        mock_select.return_value.ask.return_value = "pure-cloud"
        # First confirm: configuration panel (yes)
        mock_confirm.return_value.ask.return_value = True

        with patch("os.system"), patch("builtins.input"):
            select_execution_mode("/fake/.env")

        # Should have called _set_key for TALOS_EXECUTION_MODE + routing keys
        call_keys = {args[1] for args, _ in mock_set_key.call_args_list}
        self.assertIn("TALOS_EXECUTION_MODE", call_keys)
        self.assertIn("TALOS_FAST_ROUTING", call_keys)
        self.assertIn("TALOS_HEAVY_ROUTING", call_keys)

    @patch("src.ai.llm.model_manager._set_key")
    @patch("src.ai.llm.model_manager.dotenv_values")
    @patch("src.ai.llm.model_manager.questionary.select")
    @patch("src.ai.llm.model_manager.questionary.confirm")
    def test_execution_mode_decline_confirmation(
        self, mock_confirm, mock_select, mock_dotenv_values, mock_set_key
    ):
        """When user selects a mode but declines confirmation, _set_key should NOT be called."""
        from src.ai.llm.model_manager import select_execution_mode

        mock_dotenv_values.return_value = {"TALOS_EXECUTION_MODE": "local"}
        # v5.9.1: use "pure-cloud" which maps to fast=cloud, heavy=cloud
        mock_select.return_value.ask.return_value = "pure-cloud"
        # Declined confirmation
        mock_confirm.return_value.ask.return_value = False

        with patch("os.system"), patch("builtins.input"):
            select_execution_mode("/fake/.env")

        mock_set_key.assert_not_called()

    @patch("src.ai.llm.model_manager.questionary.select")
    @patch("src.ai.llm.model_manager.questionary.confirm")
    @patch("src.ai.llm.model_manager.dotenv_values")
    @patch("src.ai.llm.model_manager.check_ollama_alive")
    def test_embedding_model_cancel_via_sentinel(
        self, mock_ollama, mock_dotenv, mock_confirm, mock_select
    ):
        """When user cancels embedding selection, should return without changes."""
        from src.ai.llm.model_manager import select_embedding_model

        mock_ollama.return_value = True
        mock_dotenv.return_value = {"LOCAL_EMBEDDING_MODEL": ""}
        mock_select.return_value.ask.return_value = "__cancel__"

        with patch("os.system"), patch("builtins.input"):
            select_embedding_model("/fake/.env")

        # Should not raise -- graceful return


if __name__ == "__main__":
    unittest.main()
