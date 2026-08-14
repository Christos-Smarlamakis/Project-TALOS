# -*- coding: utf-8 -*-
"""
Module: test_provisioner.py
Project: TALOS v5.9.17
Description:
    Unit tests for the isolated frontend provisioner (frontend_provisioner.py).
    Tests cover OS/arch detection, MCP config generation, target directory
    resolution, architecture-aware download URL resolution (dynamic API +
    fallback), per-platform asset matching with priority rules and exclusion
    lists, and the full provisioning pipeline.

    Key design decisions:
    - Mock all network, filesystem, and platform calls for hermeticity.
    - Tests verify logic without actual downloads.
    - MCP config structure is validated for correctness.
    - Architecture detection is tested across x64/arm64/unknown variants.
    - Per-platform asset matching is tested with realistic GitHub release
      payloads covering priority ordering and exclusion behavior.

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
# -- Architecture Detection Tests --
# ------------------------------------------------------------------

class TestArchitectureDetection:
    """Tests for the _detect_architecture function."""

    def test_detect_x86_64(self):
        """Verify x86_64 machine returns 'x64'."""
        with patch('platform.machine', return_value='x86_64'):
            from src.utils.frontend_provisioner import _detect_architecture
            assert _detect_architecture() == 'x64'

    def test_detect_amd64(self):
        """Verify amd64 machine returns 'x64'."""
        with patch('platform.machine', return_value='amd64'):
            from src.utils.frontend_provisioner import _detect_architecture
            assert _detect_architecture() == 'x64'

    def test_detect_x64(self):
        """Verify x64 machine returns 'x64'."""
        with patch('platform.machine', return_value='x64'):
            from src.utils.frontend_provisioner import _detect_architecture
            assert _detect_architecture() == 'x64'

    def test_detect_arm64(self):
        """Verify arm64 machine returns 'arm64'."""
        with patch('platform.machine', return_value='arm64'):
            from src.utils.frontend_provisioner import _detect_architecture
            assert _detect_architecture() == 'arm64'

    def test_detect_aarch64(self):
        """Verify aarch64 machine returns 'arm64'."""
        with patch('platform.machine', return_value='aarch64'):
            from src.utils.frontend_provisioner import _detect_architecture
            assert _detect_architecture() == 'arm64'

    def test_unknown_arch_defaults_to_x64(self):
        """Verify unknown machine defaults to 'x64'."""
        with patch('platform.machine', return_value='riscv64'):
            from src.utils.frontend_provisioner import _detect_architecture
            assert _detect_architecture() == 'x64'


# ------------------------------------------------------------------
# -- Arch Matches Helper Tests --
# ------------------------------------------------------------------

class TestArchMatches:
    """Tests for the _arch_matches helper."""

    def test_x64_target_returns_true_for_amd64_keyword(self):
        """Verify x64 target matches 'amd64' in combined string."""
        from src.utils.frontend_provisioner import _arch_matches
        assert _arch_matches("Cherry-Studio-amd64.AppImage", "x64") is True

    def test_x64_target_returns_false_for_arm64_keyword(self):
        """Verify x64 target rejects string containing 'arm64'."""
        from src.utils.frontend_provisioner import _arch_matches
        assert _arch_matches("Cherry-Studio-arm64.dmg", "x64") is False

    def test_arm64_target_returns_true_for_aarch64(self):
        """Verify arm64 target matches 'aarch64'."""
        from src.utils.frontend_provisioner import _arch_matches
        assert _arch_matches("app-aarch64.AppImage", "arm64") is True

    def test_arm64_target_returns_false_for_x86_64(self):
        """Verify arm64 target rejects 'x86_64'."""
        from src.utils.frontend_provisioner import _arch_matches
        assert _arch_matches("app-x86_64.tar.gz", "arm64") is False


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
        assert "TALOS v5.8.2" in server["description"]

    def test_generate_config_writes_file(self):
        """Verify that generate_mcp_config writes to a file when path is given."""
        from src.utils.frontend_provisioner import generate_mcp_config
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mcp_config.json"
            config = generate_mcp_config(output_path=output_path)
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
            assert "TALOS v5.8.2" in content

    def test_provision_full_succeeds_even_if_download_fails(self):
        """Verify that provision_full continues even if download fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import provision_full
            target = Path(tmpdir) / "ui_test"
            with patch(
                'src.utils.frontend_provisioner.download_cherry_studio',
                return_value=False,
            ):
                success = provision_full(target_dir=target)
                assert (target / "mcp_config.json").exists()
                assert (target / "LAUNCH_INSTRUCTIONS.txt").exists()


# ------------------------------------------------------------------
# -- Fallback URL Tests --
# ------------------------------------------------------------------

class TestFallbackURLs:
    """Tests verifying fallback download URL integrity per OS."""

    def test_windows_fallback_is_portable_exe(self):
        """Verify Windows fallback URL is a portable .exe with x64."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS
        url = _FALLBACK_URLS.get("Windows", "")
        assert "portable.exe" in url
        assert "x64" in url

    def test_linux_fallback_is_appimage(self):
        """Verify Linux fallback URL is an x86_64 .AppImage."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS
        url = _FALLBACK_URLS.get("Linux", "")
        assert ".AppImage" in url
        assert "x86_64" in url

    def test_macos_fallback_is_arm64_dmg(self):
        """Verify macOS fallback URL is an arm64 .dmg."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS
        url = _FALLBACK_URLS.get("Darwin", "")
        assert ".dmg" in url
        assert "arm64" in url

    def test_all_supported_os_have_fallback_urls(self):
        """Verify that all supported OS have fallback download URLs."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS, _SUPPORTED_OS
        for os_name in _SUPPORTED_OS:
            assert os_name in _FALLBACK_URLS, f"Missing fallback URL for OS: {os_name}"
            assert _FALLBACK_URLS[os_name], f"Empty fallback URL for OS: {os_name}"

    def test_fallback_version_is_v1_9_12(self):
        """Verify the fallback version targets a valid known-good release."""
        from src.utils.frontend_provisioner import _FALLBACK_VERSION
        assert _FALLBACK_VERSION == "1.9.12"

    def test_fallback_urls_contain_fallback_version(self):
        """Verify fallback URLs embed the correct version string."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS, _FALLBACK_VERSION
        for os_name, url in _FALLBACK_URLS.items():
            assert _FALLBACK_VERSION in url, (
                f"Fallback URL for {os_name} does not contain version {_FALLBACK_VERSION}"
            )

    def test_windows_fallback_excludes_installers(self):
        """Verify Windows fallback URL contains no installer indicators."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS
        url = _FALLBACK_URLS.get("Windows", "").lower()
        assert "setup" not in url
        assert "nsis" not in url
        assert ".msi" not in url

    def test_linux_fallback_excludes_package_formats(self):
        """Verify Linux fallback URL contains no .deb/.rpm/tar.gz/zip."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS
        url = _FALLBACK_URLS.get("Linux", "").lower()
        assert ".deb" not in url
        assert ".rpm" not in url
        assert ".tar.gz" not in url
        assert ".zip" not in url

    def test_macos_fallback_excludes_cross_platform(self):
        """Verify macOS fallback URL contains no Windows/Linux artifacts."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS
        url = _FALLBACK_URLS.get("Darwin", "").lower()
        assert ".exe" not in url
        assert ".appimage" not in url
        assert ".deb" not in url
        assert ".rpm" not in url


# ------------------------------------------------------------------
# -- GitHub API Asset Resolution Tests --
# ------------------------------------------------------------------

# Sample GitHub release JSON payload simulating Cherry Studio v2.0.0.
_SAMPLE_RELEASE_JSON = {
    "tag_name": "v2.0.0",
    "assets": [
        # Windows portable assets
        {
            "name": "Cherry-Studio-2.0.0-x64-portable.exe",
            "browser_download_url": (
                "https://github.com/CherryHQ/cherry-studio/releases/download/"
                "v2.0.0/Cherry-Studio-2.0.0-x64-portable.exe"
            ),
        },
        {
            "name": "Cherry-Studio-2.0.0-win-x64.zip",
            "browser_download_url": (
                "https://github.com/CherryHQ/cherry-studio/releases/download/"
                "v2.0.0/Cherry-Studio-2.0.0-win-x64.zip"
            ),
        },
        # Linux portable asset
        {
            "name": "Cherry-Studio-2.0.0-x86_64.AppImage",
            "browser_download_url": (
                "https://github.com/CherryHQ/cherry-studio/releases/download/"
                "v2.0.0/Cherry-Studio-2.0.0-x86_64.AppImage"
            ),
        },
        # macOS portable assets
        {
            "name": "Cherry-Studio-2.0.0-arm64.dmg",
            "browser_download_url": (
                "https://github.com/CherryHQ/cherry-studio/releases/download/"
                "v2.0.0/Cherry-Studio-2.0.0-arm64.dmg"
            ),
        },
    ],
}


class TestGetCherryVersionFromRelease:
    """Tests for _get_cherry_version_from_release."""

    def test_strips_leading_v(self):
        """Verify the leading 'v' is stripped from tag_name."""
        from src.utils.frontend_provisioner import _get_cherry_version_from_release
        assert _get_cherry_version_from_release({"tag_name": "v2.0.0"}) == "2.0.0"

    def test_no_v_prefix_preserved(self):
        """Verify version without 'v' prefix is returned as-is."""
        from src.utils.frontend_provisioner import _get_cherry_version_from_release
        assert _get_cherry_version_from_release({"tag_name": "2.0.0"}) == "2.0.0"

    def test_missing_tag_falls_back(self):
        """Verify missing tag_name returns fallback version."""
        from src.utils.frontend_provisioner import _get_cherry_version_from_release
        assert _get_cherry_version_from_release({}) == "1.9.12"


class TestMatchWindowsAsset:
    """Tests for _match_windows_asset with architecture awareness."""

    def test_windows_x64_portable_exe_selected(self):
        """Verify x64 portable .exe is selected on x64 arch."""
        from src.utils.frontend_provisioner import _match_windows_asset
        assets = _SAMPLE_RELEASE_JSON["assets"]
        url = _match_windows_asset(assets, "x64")
        assert url is not None
        assert "x64-portable.exe" in url
        assert "setup" not in url.lower()

    def test_windows_rejects_setup_exe(self):
        """Verify Windows rejects setup.exe installers."""
        from src.utils.frontend_provisioner import _match_windows_asset
        assets = [
            {
                "name": "Cherry-Studio-Setup-2.0.0.exe",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-Setup-2.0.0.exe"
                ),
            },
            {
                "name": "Cherry-Studio-2.0.0-x64-portable.exe",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-x64-portable.exe"
                ),
            },
        ]
        url = _match_windows_asset(assets, "x64")
        assert url is not None
        assert "portable" in url
        assert "setup" not in url.lower()

    def test_windows_rejects_nsis_installer(self):
        """Verify Windows rejects NSIS installer assets."""
        from src.utils.frontend_provisioner import _match_windows_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-nsis-setup.exe",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-nsis-setup.exe"
                ),
            },
        ]
        url = _match_windows_asset(assets, "x64")
        assert url is None

    def test_windows_rejects_msi(self):
        """Verify Windows rejects .msi assets."""
        from src.utils.frontend_provisioner import _match_windows_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0.msi",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0.msi"
                ),
            },
        ]
        url = _match_windows_asset(assets, "x64")
        assert url is None

    def test_windows_rejects_macos_dmg(self):
        """Verify Windows rejects .dmg (macOS) assets."""
        from src.utils.frontend_provisioner import _match_windows_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0.dmg",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0.dmg"
                ),
            },
        ]
        url = _match_windows_asset(assets, "x64")
        assert url is None

    def test_windows_falls_back_to_zip_when_no_portable_exe(self):
        """Verify Windows falls back to win-x64.zip when no portable .exe exists."""
        from src.utils.frontend_provisioner import _match_windows_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-win-x64.zip",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-win-x64.zip"
                ),
            },
        ]
        url = _match_windows_asset(assets, "x64")
        assert url is not None
        assert ".zip" in url

    def test_windows_arm64_portable_exe_selected(self):
        """Verify arm64 portable .exe is selected on arm64 arch."""
        from src.utils.frontend_provisioner import _match_windows_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-x64-portable.exe",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-x64-portable.exe"
                ),
            },
            {
                "name": "Cherry-Studio-2.0.0-arm64-portable.exe",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-arm64-portable.exe"
                ),
            },
        ]
        url = _match_windows_asset(assets, "arm64")
        assert url is not None
        assert "arm64-portable.exe" in url


class TestMatchLinuxAsset:
    """Tests for _match_linux_asset with architecture awareness."""

    def test_linux_x86_64_appimage_selected(self):
        """Verify x86_64 .AppImage is selected on x64 arch."""
        from src.utils.frontend_provisioner import _match_linux_asset
        assets = _SAMPLE_RELEASE_JSON["assets"]
        url = _match_linux_asset(assets, "x64")
        assert url is not None
        assert ".AppImage" in url
        assert "x86_64" in url

    def test_linux_rejects_deb(self):
        """Verify Linux rejects .deb packages."""
        from src.utils.frontend_provisioner import _match_linux_asset
        assets = [
            {
                "name": "cherry-studio_2.0.0_amd64.deb",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/cherry-studio_2.0.0_amd64.deb"
                ),
            },
        ]
        url = _match_linux_asset(assets, "x64")
        assert url is None

    def test_linux_rejects_rpm(self):
        """Verify Linux rejects .rpm packages."""
        from src.utils.frontend_provisioner import _match_linux_asset
        assets = [
            {
                "name": "cherry-studio-2.0.0.x86_64.rpm",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/cherry-studio-2.0.0.x86_64.rpm"
                ),
            },
        ]
        url = _match_linux_asset(assets, "x64")
        assert url is None

    def test_linux_rejects_tar_gz(self):
        """Verify Linux rejects .tar.gz archives."""
        from src.utils.frontend_provisioner import _match_linux_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-linux-x64.tar.gz",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-linux-x64.tar.gz"
                ),
            },
        ]
        url = _match_linux_asset(assets, "x64")
        assert url is None

    def test_linux_rejects_windows_exe(self):
        """Verify Linux rejects .exe cross-platform artifacts."""
        from src.utils.frontend_provisioner import _match_linux_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0.exe",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0.exe"
                ),
            },
        ]
        url = _match_linux_asset(assets, "x64")
        assert url is None

    def test_linux_arm64_appimage_selected(self):
        """Verify aarch64 .AppImage is selected on arm64 arch."""
        from src.utils.frontend_provisioner import _match_linux_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-aarch64.AppImage",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-aarch64.AppImage"
                ),
            },
        ]
        url = _match_linux_asset(assets, "arm64")
        assert url is not None
        assert "aarch64.AppImage" in url


class TestMatchMacOSAsset:
    """Tests for _match_macos_asset with architecture awareness."""

    def test_macos_arm64_dmg_selected(self):
        """Verify arm64 .dmg is selected on arm64 arch."""
        from src.utils.frontend_provisioner import _match_macos_asset
        assets = _SAMPLE_RELEASE_JSON["assets"]
        url = _match_macos_asset(assets, "arm64")
        assert url is not None
        assert "arm64.dmg" in url

    def test_macos_zip_fallback(self):
        """Verify arch-specific .zip is selected when no .dmg matches."""
        from src.utils.frontend_provisioner import _match_macos_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-x64.zip",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-x64.zip"
                ),
            },
        ]
        url = _match_macos_asset(assets, "x64")
        assert url is not None
        assert "x64.zip" in url

    def test_macos_rejects_exe(self):
        """Verify macOS rejects .exe cross-platform artifacts."""
        from src.utils.frontend_provisioner import _match_macos_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-x64-portable.exe",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-x64-portable.exe"
                ),
            },
        ]
        url = _match_macos_asset(assets, "arm64")
        assert url is None

    def test_macos_rejects_appimage(self):
        """Verify macOS rejects .AppImage artifacts."""
        from src.utils.frontend_provisioner import _match_macos_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-x86_64.AppImage",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-x86_64.AppImage"
                ),
            },
        ]
        url = _match_macos_asset(assets, "arm64")
        assert url is None

    def test_macos_universal_dmg_fallback(self):
        """Verify universal .dmg is selected when no arch-specific match exists."""
        from src.utils.frontend_provisioner import _match_macos_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-universal.dmg",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-universal.dmg"
                ),
            },
        ]
        url = _match_macos_asset(assets, "arm64")
        assert url is not None
        assert "universal.dmg" in url

    def test_macos_universal_zip_fallback(self):
        """Verify universal .zip is the last-resort fallback."""
        from src.utils.frontend_provisioner import _match_macos_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-universal.zip",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-universal.zip"
                ),
            },
        ]
        url = _match_macos_asset(assets, "arm64")
        assert url is not None
        assert "universal.zip" in url

    def test_macos_dmg_priority_over_zip(self):
        """Verify arch-specific .dmg takes priority over arch-specific .zip."""
        from src.utils.frontend_provisioner import _match_macos_asset
        assets = [
            {
                "name": "Cherry-Studio-2.0.0-arm64.zip",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-arm64.zip"
                ),
            },
            {
                "name": "Cherry-Studio-2.0.0-arm64.dmg",
                "browser_download_url": (
                    "https://github.com/CherryHQ/cherry-studio/releases/download/"
                    "v2.0.0/Cherry-Studio-2.0.0-arm64.dmg"
                ),
            },
        ]
        url = _match_macos_asset(assets, "arm64")
        assert url is not None
        assert ".dmg" in url  # .dmg has priority 1 over .zip priority 2


class TestResolveDownloadURLs:
    """Tests for _resolve_download_urls."""

    def test_resolve_from_sample_api_response(self):
        """Verify URL resolution from a valid GitHub API response."""
        from src.utils.frontend_provisioner import _resolve_download_urls
        with patch(
            'src.utils.frontend_provisioner._fetch_latest_release_assets',
            return_value=_SAMPLE_RELEASE_JSON,
        ):
            with patch('platform.machine', return_value='x86_64'):
                version, urls = _resolve_download_urls()
                assert version == "2.0.0"
                assert "Windows" in urls
                assert "Linux" in urls
                assert "Darwin" in urls
                assert "x64-portable.exe" in urls["Windows"]
                assert ".AppImage" in urls["Linux"]
                # On x86_64 machine, macOS matches arm64.dmg from sample (no x64 .dmg)
                # so _match_macos_asset will look for arch match first then universal.
                # With only arm64.dmg in sample, x64 won't match arch, so falls through.
                # Verify Darwin URL is not None.
                assert urls["Darwin"] is not None

    def test_resolve_falls_back_when_api_fails(self):
        """Verify fallback URLs are used when the API returns None."""
        from src.utils.frontend_provisioner import _resolve_download_urls, _FALLBACK_VERSION
        with patch(
            'src.utils.frontend_provisioner._fetch_latest_release_assets',
            return_value=None,
        ):
            version, urls = _resolve_download_urls()
            assert version == _FALLBACK_VERSION
            assert "portable.exe" in urls["Windows"]
            assert ".AppImage" in urls["Linux"]
            assert ".dmg" in urls["Darwin"]

    def test_resolve_falls_back_when_assets_empty(self):
        """Verify fallback when release JSON has no assets array."""
        from src.utils.frontend_provisioner import _resolve_download_urls
        empty_release = {"tag_name": "v3.0.0", "assets": []}
        with patch(
            'src.utils.frontend_provisioner._fetch_latest_release_assets',
            return_value=empty_release,
        ):
            version, urls = _resolve_download_urls()
            assert version == "1.9.12"


class TestFetchLatestReleaseAssets:
    """Tests for _fetch_latest_release_assets."""

    def test_returns_parsed_json_on_success(self):
        """Verify the function parses JSON correctly on HTTP 200."""
        from src.utils.frontend_provisioner import _fetch_latest_release_assets
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(_SAMPLE_RELEASE_JSON).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = _fetch_latest_release_assets()
            assert result is not None
            assert result["tag_name"] == "v2.0.0"

    def test_returns_none_on_http_error(self):
        """Verify None is returned on HTTP error."""
        from src.utils.frontend_provisioner import _fetch_latest_release_assets
        import urllib.error
        with patch(
            'urllib.request.urlopen',
            side_effect=urllib.error.HTTPError(
                "https://api.github.com", 403, "Rate limited", {}, None
            ),
        ):
            result = _fetch_latest_release_assets()
            assert result is None

    def test_returns_none_on_url_error(self):
        """Verify None is returned on URLError (network failure)."""
        from src.utils.frontend_provisioner import _fetch_latest_release_assets
        import urllib.error
        with patch(
            'urllib.request.urlopen',
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            result = _fetch_latest_release_assets()
            assert result is None


# ------------------------------------------------------------------
# -- Skip Already Provisioned Tests --
# ------------------------------------------------------------------

class TestSkipAlreadyProvisioned:
    """Tests for the force flag and already-provisioned detection."""

    def test_download_skips_if_marker_exists(self):
        """Verify download is skipped when .cherry_installed marker exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import download_cherry_studio

            marker = Path(tmpdir) / ".cherry_installed"
            marker.write_text("version=1.2.3\nos=Linux\n")

            with patch('platform.system', return_value='Linux'):
                result = download_cherry_studio(target_dir=Path(tmpdir))
                assert result is True  # Should return True (already installed).

    def test_download_with_force_overrides_marker(self):
        """Verify that force=True bypasses the marker check and proceeds to download."""
        from src.utils.frontend_provisioner import download_cherry_studio

        fallback_url = (
            "https://github.com/CherryHQ/cherry-studio/releases/download/"
            "v1.9.12/Cherry-Studio-1.9.12-x64-portable.exe"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            marker = Path(tmpdir) / ".cherry_installed"
            marker.write_text("version=1.2.3\nos=Windows\n")

            with patch('platform.system', return_value='Windows'):
                with patch('platform.machine', return_value='x86_64'):
                    with patch(
                        'src.utils.frontend_provisioner._resolve_download_urls',
                        return_value=("1.9.12", {"Windows": fallback_url}),
                    ):
                        with patch('urllib.request.urlretrieve'):
                            with patch('shutil.unpack_archive'):
                                with patch('os.unlink'):
                                    result = download_cherry_studio(
                                        target_dir=Path(tmpdir), force=True,
                                    )
                                    assert result is True


# ------------------------------------------------------------------
# -- Constants Validation Tests --
# ------------------------------------------------------------------

class TestConstants:
    """Tests validating provisioner constants."""

    def test_fallback_version_is_string(self):
        """Verify _FALLBACK_VERSION is a non-empty string."""
        from src.utils.frontend_provisioner import _FALLBACK_VERSION
        assert isinstance(_FALLBACK_VERSION, str)
        assert len(_FALLBACK_VERSION) > 0

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

    def test_user_agent_contains_version(self):
        """Verify the User-Agent header includes the TALOS version."""
        from src.utils.frontend_provisioner import _USER_AGENT
        assert "TALOS" in _USER_AGENT
        assert "5.8.2" in _USER_AGENT

    def test_windows_exclude_has_installer_keywords(self):
        """Verify _WINDOWS_EXCLUDE contains setup/nsis/msi/mac/dmg entries."""
        from src.utils.frontend_provisioner import _WINDOWS_EXCLUDE
        assert "setup.exe" in _WINDOWS_EXCLUDE
        assert "nsis" in _WINDOWS_EXCLUDE
        assert ".msi" in _WINDOWS_EXCLUDE
        assert ".dmg" in _WINDOWS_EXCLUDE

    def test_linux_exclude_has_package_keywords(self):
        """Verify _LINUX_EXCLUDE contains .deb/.rpm/.tar.gz/.zip/.exe."""
        from src.utils.frontend_provisioner import _LINUX_EXCLUDE
        assert ".deb" in _LINUX_EXCLUDE
        assert ".rpm" in _LINUX_EXCLUDE
        assert ".tar.gz" in _LINUX_EXCLUDE
        assert ".zip" in _LINUX_EXCLUDE
        assert ".exe" in _LINUX_EXCLUDE

    def test_macos_exclude_has_cross_platform_keywords(self):
        """Verify _MACOS_EXCLUDE contains .exe/.appimage/.deb/.rpm."""
        from src.utils.frontend_provisioner import _MACOS_EXCLUDE
        assert ".exe" in _MACOS_EXCLUDE
        assert ".appimage" in _MACOS_EXCLUDE
        assert ".deb" in _MACOS_EXCLUDE
        assert ".rpm" in _MACOS_EXCLUDE

    def test_arch_x64_keywords_include_variants(self):
        """Verify _ARCH_X64_KEYWORDS covers x64/x86_64/amd64/intel64."""
        from src.utils.frontend_provisioner import _ARCH_X64_KEYWORDS
        assert "x64" in _ARCH_X64_KEYWORDS
        assert "x86_64" in _ARCH_X64_KEYWORDS
        assert "amd64" in _ARCH_X64_KEYWORDS
        assert "intel64" in _ARCH_X64_KEYWORDS

    def test_arch_arm64_keywords_include_variants(self):
        """Verify _ARCH_ARM64_KEYWORDS covers arm64/aarch64."""
        from src.utils.frontend_provisioner import _ARCH_ARM64_KEYWORDS
        assert "arm64" in _ARCH_ARM64_KEYWORDS
        assert "aarch64" in _ARCH_ARM64_KEYWORDS


# ------------------------------------------------------------------
# -- Edge Cases --
# ------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases in the frontend provisioner."""

    def test_target_dir_with_trailing_slash(self):
        """Verify trailing slashes are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.utils.frontend_provisioner import resolve_target_dir
            path_with_slash = tmpdir + os.sep
            result = resolve_target_dir(project_root=path_with_slash)
            assert result.name == "cherry_ui_isolated"

    def test_mcp_config_keys_are_strings(self):
        """Verify all MCP config keys are strings (not Path objects)."""
        from src.utils.frontend_provisioner import generate_mcp_config
        config = generate_mcp_config()
        config_str = json.dumps(config)
        assert isinstance(config_str, str)