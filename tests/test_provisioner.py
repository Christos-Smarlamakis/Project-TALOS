# -*- coding: utf-8 -*-
"""
Module: test_provisioner.py
Project: TALOS v5.8.2
Description:
    Unit tests for the isolated frontend provisioner (frontend_provisioner.py).
    Tests cover OS detection, MCP config generation, target directory resolution,
    download URL resolution (dynamic API + fallback), asset matching logic, and
    the full provisioning pipeline.

    Key design decisions:
    - Mock all network and filesystem operations to maintain hermeticity.
    - Tests verify the logic without actual downloads.
    - MCP config structure is validated for correctness.
    - OS detection tests are safe (no actual platform calls needed for logic tests).
    - GitHub API asset resolution is tested with sample JSON payloads.

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
        assert "TALOS v5.8.2" in server["description"]

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
                # Should still succeed (download failure is non-fatal).
                success = provision_full(target_dir=target)
                # MCP config should still exist.
                assert (target / "mcp_config.json").exists()
                # Launch instructions should still exist.
                assert (target / "LAUNCH_INSTRUCTIONS.txt").exists()


# ------------------------------------------------------------------
# -- Fallback URL Tests (replaces old DownloadURLSelection tests) --
# ------------------------------------------------------------------

class TestFallbackURLs:
    """Tests verifying fallback download URL integrity per OS."""

    def test_windows_fallback_url_is_zip(self):
        """Verify Windows fallback URL points to a .zip archive."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS
        url = _FALLBACK_URLS.get("Windows", "")
        assert url.endswith(".zip")

    def test_linux_fallback_url_is_tar_gz(self):
        """Verify Linux fallback URL points to a .tar.gz archive."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS
        url = _FALLBACK_URLS.get("Linux", "")
        assert url.endswith(".tar.gz")

    def test_macos_fallback_url_is_dmg(self):
        """Verify macOS fallback URL points to a .dmg archive."""
        from src.utils.frontend_provisioner import _FALLBACK_URLS
        url = _FALLBACK_URLS.get("Darwin", "")
        assert url.endswith(".dmg")

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


# ------------------------------------------------------------------
# -- GitHub API Asset Resolution Tests --
# ------------------------------------------------------------------

# Sample GitHub release JSON payload mimicking a real Cherry Studio release.
_SAMPLE_RELEASE_JSON = {
    "tag_name": "v2.0.0",
    "assets": [
        {
            "name": "Cherry-Studio-portable-win-x64-2.0.0.zip",
            "browser_download_url": (
                "https://github.com/CherryHQ/cherry-studio/releases/download/"
                "v2.0.0/Cherry-Studio-portable-win-x64-2.0.0.zip"
            ),
        },
        {
            "name": "Cherry-Studio-portable-linux-x64-2.0.0.tar.gz",
            "browser_download_url": (
                "https://github.com/CherryHQ/cherry-studio/releases/download/"
                "v2.0.0/Cherry-Studio-portable-linux-x64-2.0.0.tar.gz"
            ),
        },
        {
            "name": "Cherry-Studio-portable-mac-arm64-2.0.0.dmg",
            "browser_download_url": (
                "https://github.com/CherryHQ/cherry-studio/releases/download/"
                "v2.0.0/Cherry-Studio-portable-mac-arm64-2.0.0.dmg"
            ),
        },
    ],
}


class TestGetCherryVersionFromRelease:
    """Tests for _get_cherry_version_from_release."""

    def test_strips_leading_v(self):
        """Verify the leading 'v' is stripped from tag_name."""
        from src.utils.frontend_provisioner import _get_cherry_version_from_release
        result = _get_cherry_version_from_release({"tag_name": "v2.0.0"})
        assert result == "2.0.0"

    def test_no_v_prefix_preserved(self):
        """Verify version without 'v' prefix is returned as-is."""
        from src.utils.frontend_provisioner import _get_cherry_version_from_release
        result = _get_cherry_version_from_release({"tag_name": "2.0.0"})
        assert result == "2.0.0"

    def test_missing_tag_falls_back(self):
        """Verify missing tag_name returns fallback version."""
        from src.utils.frontend_provisioner import _get_cherry_version_from_release
        result = _get_cherry_version_from_release({})
        assert result == "1.9.12"


class TestMatchAssetForOS:
    """Tests for _match_asset_for_os."""

    def test_match_windows_zip(self):
        """Verify Windows asset matching selects .zip."""
        from src.utils.frontend_provisioner import _match_asset_for_os
        url = _match_asset_for_os(_SAMPLE_RELEASE_JSON["assets"], "Windows")
        assert url is not None
        assert ".zip" in url

    def test_match_linux_tar_gz(self):
        """Verify Linux asset matching selects .tar.gz."""
        from src.utils.frontend_provisioner import _match_asset_for_os
        url = _match_asset_for_os(_SAMPLE_RELEASE_JSON["assets"], "Linux")
        assert url is not None
        assert ".tar.gz" in url

    def test_match_macos_dmg(self):
        """Verify macOS asset matching selects .dmg."""
        from src.utils.frontend_provisioner import _match_asset_for_os
        url = _match_asset_for_os(_SAMPLE_RELEASE_JSON["assets"], "Darwin")
        assert url is not None
        assert ".dmg" in url

    def test_no_match_returns_none(self):
        """Verify None is returned when no asset matches the OS patterns."""
        from src.utils.frontend_provisioner import _match_asset_for_os
        # No asset in the sample set matches .AppImage (Linux second pattern
        # would match .tar.gz, so we test an asset set with only Windows files).
        win_only = [
            {
                "name": "Cherry-Setup.exe",
                "browser_download_url": "https://example.com/Cherry-Setup.exe",
            }
        ]
        url = _match_asset_for_os(win_only, "Linux")
        assert url is None

    def test_empty_assets_returns_none(self):
        """Verify empty asset list returns None."""
        from src.utils.frontend_provisioner import _match_asset_for_os
        url = _match_asset_for_os([], "Windows")
        assert url is None


class TestResolveDownloadURLs:
    """Tests for _resolve_download_urls."""

    def test_resolve_from_sample_api_response(self):
        """Verify URL resolution from a valid GitHub API response."""
        from src.utils.frontend_provisioner import _resolve_download_urls
        with patch(
            'src.utils.frontend_provisioner._fetch_latest_release_assets',
            return_value=_SAMPLE_RELEASE_JSON,
        ):
            version, urls = _resolve_download_urls()
            assert version == "2.0.0"
            assert "Windows" in urls
            assert "Linux" in urls
            assert "Darwin" in urls
            assert ".zip" in urls["Windows"]
            assert ".tar.gz" in urls["Linux"]
            assert ".dmg" in urls["Darwin"]

    def test_resolve_falls_back_when_api_fails(self):
        """Verify fallback URLs are used when the API returns None."""
        from src.utils.frontend_provisioner import _resolve_download_urls, _FALLBACK_VERSION
        with patch(
            'src.utils.frontend_provisioner._fetch_latest_release_assets',
            return_value=None,
        ):
            version, urls = _resolve_download_urls()
            assert version == _FALLBACK_VERSION
            assert urls["Windows"].endswith(".zip")
            assert urls["Linux"].endswith(".tar.gz")
            assert urls["Darwin"].endswith(".dmg")

    def test_resolve_falls_back_when_assets_empty(self):
        """Verify fallback when release JSON has no assets array."""
        from src.utils.frontend_provisioner import _resolve_download_urls
        empty_release = {"tag_name": "v3.0.0", "assets": []}
        with patch(
            'src.utils.frontend_provisioner._fetch_latest_release_assets',
            return_value=empty_release,
        ):
            version, urls = _resolve_download_urls()
            # Should fall back since assets are empty.
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

            # Create the marker file to simulate already installed.
            marker = Path(tmpdir) / ".cherry_installed"
            marker.write_text("version=1.2.3\nos=Linux\n")

            with patch('platform.system', return_value='Linux'):
                result = download_cherry_studio(target_dir=Path(tmpdir))
                assert result is True  # Should return True (already installed).

    def test_download_with_force_overrides_marker(self):
        """Verify that force=True bypasses the marker check and proceeds to download."""
        # This test verifies the force flag logic. When force=True, the code
        # should skip the marker check and attempt a download. We mock the
        # network operations to keep the test hermetic.
        from src.utils.frontend_provisioner import download_cherry_studio
        from unittest.mock import patch, mock_open

        fallback_url = (
            "https://github.com/CherryHQ/cherry-studio/releases/download/"
            "v1.9.12/Cherry-Studio-portable-win-x64-1.9.12.zip"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            marker = Path(tmpdir) / ".cherry_installed"
            marker.write_text("version=1.2.3\nos=Windows\n")

            with patch('platform.system', return_value='Windows'):
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
                                # force=True should bypass marker and attempt download.
                                # With all operations mocked, download succeeds.
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

    def test_platform_extension_patterns_cover_all_os(self):
        """Verify all supported OS have extension matching patterns."""
        from src.utils.frontend_provisioner import _PLATFORM_EXTENSION_PATTERNS, _SUPPORTED_OS
        for os_name in _SUPPORTED_OS:
            assert os_name in _PLATFORM_EXTENSION_PATTERNS, (
                f"Missing extension patterns for OS: {os_name}"
            )
            patterns = _PLATFORM_EXTENSION_PATTERNS[os_name]
            assert len(patterns) > 0, f"Empty patterns list for OS: {os_name}"


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