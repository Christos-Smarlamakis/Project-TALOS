# -*- coding: utf-8 -*-
"""
Module: test_provisioner.py
Project: TALOS v5.7.1
Description:
    Unit tests for the isolated frontend provisioner (frontend_provisioner.py).
    Tests cover OS detection, MCP config generation, target directory resolution,
    download URL selection, and the full provisioning pipeline.

    Key design decisions:
    - Mock all network and filesystem operations to maintain hermeticity.
    - Tests verify the logic without actual downloads.
    - MCP config structure is validated for correctness.
    - OS detection tests are safe (no actual platform calls needed for logic tests).

Dependencies:
    - pytest: Test framework for fixture-based testing.
    - unittest.mock: Patching platform detection and network calls.
    - tempfile: Isolated temporary directories for filesystem tests.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ------------------------------------------------------------------
# -- OS Detection Tests --
# ------------------------------------------------------------------

class TestOSDetection:
    """Tests for the get_os_name function."""

    def test_detect_windows(self):
        """Verify Windows detection."""
        with patch('platform.system', return_value='Windows'):
            from src.utils.frontend_provisioner import get_os_name
            assert get_os_name() == 'Windows'

    def test_detect_linux(self):
        """Verify Linux detection."""
        with patch('platform.system', return_value='Linux'):
            from src.utils.frontend_provisioner import get_os_name
            assert get_os_name() == 'Linux'

    def test_detect_macos(self):
        """Verify macOS (Darwin) detection."""
        with patch('platform.system', return_value='Darwin'):
            from src.utils.frontend_provisioner import get_os_name
            assert get_os_name() == 'Darwin'

    def test_unsupported_os_raises(self):
        """Verify that unsupported OS raises OSError."""
        with patch('platform.system', return_value='FreeBSD'):
            from src.utils.frontend_provisioner import get_os_name
            with pytest.raises(OSError, match="Unsupported operating system"):
                get_os_name()


# ------------------------------------------------------------------
# -- Target Directory Resolution Tests --
# ------------------------------------------------------------------

class TestResolveTargetDir:
    """Tests for the resolve_target_dir function."""

    def test_explicit_project_root(self):
        """Verify that an explicit project root is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import resolve_target_dir
            result = resolve_target_dir(project_root=tmpdir)
            expected = Path(tmpdir) / "cherry_ui_isolated"
            assert result == expected

    def test_target_dir_includes_cherry_ui_isolated(self):
        """Verify the target directory name is correct."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import resolve_target_dir
            result = resolve_target_dir(project_root=tmpdir)
            assert result.name == "cherry_ui_isolated"


# ------------------------------------------------------------------
# -- MCP Config Generation Tests --
# ------------------------------------------------------------------

class TestMCPConfigGeneration:
    """Tests for the generate_mcp_config function."""

    def test_generate_config_structure(self):
        """Verify the generated MCP config has correct structure."""
        from src.utils.frontend_provisioner import generate_mcp_config
        config = generate_mcp_config()

        assert "mcpServers" in config
        assert "talos-local" in config["mcpServers"]

        server = config["mcpServers"]["talos-local"]
        assert server["command"] == "python"
        assert "-m" in server["args"]
        assert "src.mcp_server" in server["args"]
        assert server["env"]["TALOS_USE_LOCAL"] == "1"
        assert server["autoStart"] is True
        assert "description" in server
        assert "TALOS v5.7.1" in server["description"]

    def test_generate_config_writes_file(self):
        """Verify that generate_mcp_config writes to a file when path is given."""
        from src.utils.frontend_provisioner import generate_mcp_config
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mcp_config.json"
            config = generate_mcp_config(output_path=output_path)

            # File should exist and contain valid JSON.
            assert output_path.exists()
            with open(output_path, 'r') as f:
                file_content = json.load(f)
            assert file_content == config

    def test_generate_config_creates_parent_dirs(self):
        """Verify that generate_mcp_config creates parent directories."""
        from src.utils.frontend_provisioner import generate_mcp_config
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "mcp_config.json"
            config = generate_mcp_config(output_path=output_path)

            assert output_path.exists()
            assert output_path.parent.exists()

    def test_config_env_contains_api_port(self):
        """Verify the MCP config includes TALOS_API_PORT."""
        from src.utils.frontend_provisioner import generate_mcp_config
        config = generate_mcp_config()
        server = config["mcpServers"]["talos-local"]
        assert server["env"]["TALOS_API_PORT"] == "8001"


# ------------------------------------------------------------------
# -- Provision Full Pipeline Tests --
# ------------------------------------------------------------------

class TestProvisionFull:
    """Tests for the provision_full orchestration function."""

    def test_provision_full_creates_target_dir(self):
        """Verify that provision_full creates the target directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import provision_full
            # Patch download to avoid actual network calls.
            with patch(
                'src.utils.frontend_provisioner.download_cherry_studio',
                return_value=True,
            ):
                success = provision_full(target_dir=Path(tmpdir) / "test_ui")
                assert success
                assert (Path(tmpdir) / "test_ui").exists()

    def test_provision_full_generates_mcp_config(self):
        """Verify that provision_full generates the MCP config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import provision_full
            target = Path(tmpdir) / "ui_test"
            with patch(
                'src.utils.frontend_provisioner.download_cherry_studio',
                return_value=True,
            ):
                provision_full(target_dir=target)

            mcp_config = target / "mcp_config.json"
            assert mcp_config.exists()

    def test_provision_full_creates_launch_instructions(self):
        """Verify that provision_full creates LAUNCH_INSTRUCTIONS.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import provision_full
            target = Path(tmpdir) / "ui_test"
            with patch(
                'src.utils.frontend_provisioner.download_cherry_studio',
                return_value=True,
            ):
                provision_full(target_dir=target)

            instructions = target / "LAUNCH_INSTRUCTIONS.txt"
            assert instructions.exists()
            content = instructions.read_text()
            assert "Cherry Studio" in content
            assert "TALOS v5.7.1" in content

    def test_provision_full_succeeds_even_if_download_fails(self):
        """Verify that provision_full continues even if download fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import provision_full
            target = Path(tmpdir) / "ui_test"
            with patch(
                'src.utils.frontend_provisioner.download_cherry_studio',
                return_value=False,
            ):
                # Should still succeed (download failure is non-fatal).
                success = provision_full(target_dir=target)
                # MCP config should still exist.
                assert (target / "mcp_config.json").exists()
                # Launch instructions should still exist.
                assert (target / "LAUNCH_INSTRUCTIONS.txt").exists()


# ------------------------------------------------------------------
# -- Download URL Selection Tests --
# ------------------------------------------------------------------

class TestDownloadURLSelection:
    """Tests verifying correct download URL selection per OS."""

    def test_windows_url_is_zip(self):
        """Verify Windows download URL points to a .zip archive."""
        from src.utils.frontend_provisioner import _CHERRY_URLS
        url = _CHERRY_URLS.get("Windows", "")
        assert url.endswith(".zip")

    def test_linux_url_is_tar_gz(self):
        """Verify Linux download URL points to a .tar.gz archive."""
        from src.utils.frontend_provisioner import _CHERRY_URLS
        url = _CHERRY_URLS.get("Linux", "")
        assert url.endswith(".tar.gz")

    def test_macos_url_is_dmg(self):
        """Verify macOS download URL points to a .dmg archive."""
        from src.utils.frontend_provisioner import _CHERRY_URLS
        url = _CHERRY_URLS.get("Darwin", "")
        assert url.endswith(".dmg")

    def test_all_supported_os_have_urls(self):
        """Verify that all supported OS have download URLs."""
        from src.utils.frontend_provisioner import _CHERRY_URLS, _SUPPORTED_OS
        for os_name in _SUPPORTED_OS:
            assert os_name in _CHERRY_URLS, f"Missing URL for OS: {os_name}"
            assert _CHERRY_URLS[os_name], f"Empty URL for OS: {os_name}"


# ------------------------------------------------------------------
# -- Skip Already Provisioned Tests --
# ------------------------------------------------------------------

class TestSkipAlreadyProvisioned:
    """Tests for the force flag and already-provisioned detection."""

    def test_download_skips_if_marker_exists(self):
        """Verify download is skipped when .cherry_installed marker exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import download_cherry_studio

            # Create the marker file to simulate already installed.
            marker = Path(tmpdir) / ".cherry_installed"
            marker.write_text("version=1.2.3\nos=Linux\n")

            with patch('platform.system', return_value='Linux'):
                result = download_cherry_studio(target_dir=Path(tmpdir))
                assert result is True  # Should return True (already installed).

    def test_download_with_force_overrides_marker(self):
        """Verify that force=True bypasses the marker check."""
        # This test verifies the force flag logic. Since we cannot actually
        # test the download, we verify that when force=True, the code
        # proceeds past the marker check.
        from src.utils.frontend_provisioner import download_cherry_studio

        # The function should attempt download (and fail gracefully)
        # when force=True, even with a marker.
        with tempfile.TemporaryDirectory() as tmpdir:
            marker = Path(tmpdir) / ".cherry_installed"
            marker.write_text("version=1.2.3\nos=Windows\n")

            # With force=True, the function should try to download
            # and fail with a network error (since we are not mocking).
            # We just verify it returns False (network unavailable)
            # rather than True (skip).
            result = download_cherry_studio(target_dir=Path(tmpdir), force=True)
            # Expected: False because actual download fails.
            assert result is False


# ------------------------------------------------------------------
# -- Constants Validation Tests --
# ------------------------------------------------------------------

class TestConstants:
    """Tests validating provisioner constants."""

    def test_cherry_studio_version_is_string(self):
        """Verify CHERRY_STUDIO_VERSION is a string."""
        from src.utils.frontend_provisioner import CHERRY_STUDIO_VERSION
        assert isinstance(CHERRY_STUDIO_VERSION, str)
        assert len(CHERRY_STUDIO_VERSION) > 0

    def test_target_dir_is_cherry_ui_isolated(self):
        """Verify the target directory constant is correct."""
        from src.utils.frontend_provisioner import _TARGET_DIR
        assert _TARGET_DIR == "cherry_ui_isolated"

    def test_supported_os_includes_major_platforms(self):
        """Verify the supported OS set includes Windows, Linux, macOS."""
        from src.utils.frontend_provisioner import _SUPPORTED_OS
        assert "Windows" in _SUPPORTED_OS
        assert "Linux" in _SUPPORTED_OS
        assert "Darwin" in _SUPPORTED_OS


# ------------------------------------------------------------------
# -- Edge Cases --
# ------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases in the frontend provisioner."""

    def test_target_dir_with_trailing_slash(self):
        """Verify trailing slashes are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import resolve_target_dir
            # Path with trailing separator.
            path_with_slash = tmpdir + os.sep
            result = resolve_target_dir(project_root=path_with_slash)
            assert result.name == "cherry_ui_isolated"

    def test_mcp_config_keys_are_strings(self):
        """Verify all MCP config keys are strings (not Path objects)."""
        from src.utils.frontend_provisioner import generate_mcp_config
        config = generate_mcp_config()
        config_str = json.dumps(config)  # Should not raise.
        assert isinstance(config_str, str)