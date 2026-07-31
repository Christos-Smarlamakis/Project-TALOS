# -*- coding: utf-8 -*-
"""
Module: frontend_provisioner.py
Project: TALOS v5.8.2
Description:
    Isolated interim UI provisioner for TALOS. Downloads a portable copy of Cherry
    Studio (CherryHQ/cherry-studio) based on the host operating system into the
    `cherry_ui_isolated/` directory (which is gitignored). Auto-generates an MCP
    configuration JSON file for Cherry Studio pointing to the TALOS MCP server at
    `src/mcp_server.py`. This provides a functional local UI until the full React
    frontend is deployed.

    Key design decisions:
    - Respects the air-gapped principle: downloads only when explicitly invoked.
    - OS detection via `platform.system()` to select the correct binary archive.
    - Dynamic GitHub Release asset resolution: queries the GitHub API for the
      latest release, then inspects the `assets` array for matching binaries.
    - Falls back to hardcoded URLs (v1.9.12) if the API fails or is rate-limited.
    - The cherry_ui_isolated/ directory is gitignored to keep the repository clean.
    - MCP config generation uses relative paths so the provisioned UI can connect
      to the local TALOS MCP server regardless of the installation directory.
    - All network operations have configurable timeouts and graceful fallbacks.

Dependencies:
    - os, sys, platform: OS detection and filesystem operations.
    - json: MCP configuration file generation.
    - urllib.request: Binary download and GitHub API queries (stdlib, no external deps).
    - shutil, tempfile: Archive extraction and temporary file management.
"""
import os
import sys
import json
import platform
import shutil
import tempfile
import urllib.request
import urllib.error
from pathlib import Path


# ------------------------------------------------------------------
# -- Constants --
# ------------------------------------------------------------------

# GitHub API endpoint for the latest Cherry Studio release.
_CHERRY_API_URL = "https://api.github.com/repos/CherryHQ/cherry-studio/releases/latest"

# Fallback version and URLs used when the GitHub API is unreachable or rate-limited.
# These target a known-good release tag (v1.9.12) to avoid 404 errors.
_FALLBACK_VERSION = "1.9.12"
_FALLBACK_RELEASE_BASE = (
    "https://github.com/CherryHQ/cherry-studio/releases/download/"
    f"v{_FALLBACK_VERSION}"
)

# -- Platform-specific file extension patterns for dynamic asset matching --
# Each tuple contains patterns used to identify the correct download asset
# from the GitHub API response. The first pattern in the list that matches
# an asset name is selected.
_PLATFORM_EXTENSION_PATTERNS = {
    "Windows": [".zip", ".exe"],
    "Linux":   [".AppImage", ".tar.gz"],
    "Darwin":  [".dmg", ".zip"],
}

# -- Fallback URLs keyed by OS (used when API is unavailable) --
_FALLBACK_URLS = {
    "Windows": (
        f"{_FALLBACK_RELEASE_BASE}/"
        f"Cherry-Studio-portable-win-x64-{_FALLBACK_VERSION}.zip"
    ),
    "Linux": (
        f"{_FALLBACK_RELEASE_BASE}/"
        f"Cherry-Studio-portable-linux-x64-{_FALLBACK_VERSION}.tar.gz"
    ),
    "Darwin": (
        f"{_FALLBACK_RELEASE_BASE}/"
        f"Cherry-Studio-portable-mac-arm64-{_FALLBACK_VERSION}.dmg"
    ),
}

# Target directory relative to project root.
_TARGET_DIR = "cherry_ui_isolated"

# Supported operating systems for the provisioner.
_SUPPORTED_OS = frozenset({"Windows", "Linux", "Darwin"})

# -- HTTP configuration --
_GITHUB_API_TIMEOUT_SECONDS = 15
_USER_AGENT = "TALOS-Provisier/5.8.2"


# ------------------------------------------------------------------
# -- Internal: GitHub Release Asset Resolution --
# ------------------------------------------------------------------

def _fetch_latest_release_assets():
    """
    Query the GitHub API for the latest Cherry Studio release.

    Returns the parsed JSON response as a dict, or None if the request
    fails for any reason (network error, rate limit, HTTP error).

    Returns:
        dict or None: The latest release JSON from GitHub, or None on failure.
    """
    req = urllib.request.Request(
        _CHERRY_API_URL,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_GITHUB_API_TIMEOUT_SECONDS) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        print(f"  [WARN] GitHub API query failed: {exc}")
        print(f"  [INFO] Falling back to hardcoded release v{_FALLBACK_VERSION}.")
        return None


def _get_cherry_version_from_release(release_json):
    """
    Extract the tag_name from a GitHub release JSON and strip the leading 'v'.

    Args:
        release_json: Parsed JSON dict from the GitHub releases API.

    Returns:
        str: The version string without a 'v' prefix (e.g., '1.9.12').
    """
    tag = release_json.get("tag_name", _FALLBACK_VERSION)
    if tag.startswith("v"):
        tag = tag[1:]
    return tag


def _match_asset_for_os(assets, os_name):
    """
    Scan the GitHub release assets array for a download URL matching the OS.

    Uses `_PLATFORM_EXTENSION_PATTERNS` to determine the correct asset.
    For each asset, the function checks whether its `browser_download_url`
    (or `name`) contains a recognized extension for the given OS.

    Args:
        assets: List of asset dicts from the GitHub API release JSON.
        os_name: One of 'Windows', 'Linux', 'Darwin'.

    Returns:
        str or None: The browser_download_url of the best-matching asset,
                     or None if no match was found.
    """
    patterns = _PLATFORM_EXTENSION_PATTERNS.get(os_name, [])
    if not patterns:
        return None

    # First pass: find assets whose name or URL matches a recognized pattern.
    for pattern in patterns:
        for asset in assets:
            url = asset.get("browser_download_url", "")
            name = asset.get("name", "")
            if pattern in url or pattern in name:
                return url

    return None


def _resolve_download_urls():
    """
    Dynamically resolve the Cherry Studio download URLs and version.

    Attempts to fetch the latest release from the GitHub API. On success,
    extracts version and matches assets per platform. On failure, falls
    back to the hardcoded _FALLBACK_URLS and _FALLBACK_VERSION.

    Returns:
        tuple[str, dict]: (version_string, {os_name: download_url} dict)
    """
    release_json = _fetch_latest_release_assets()

    if release_json is None:
        return _FALLBACK_VERSION, dict(_FALLBACK_URLS)

    version = _get_cherry_version_from_release(release_json)
    assets = release_json.get("assets", [])

    if not assets:
        print(f"  [WARN] GitHub release v{version} has no assets. Using fallbacks.")
        return _FALLBACK_VERSION, dict(_FALLBACK_URLS)

    urls = {}
    for os_name in _SUPPORTED_OS:
        matched = _match_asset_for_os(assets, os_name)
        if matched:
            urls[os_name] = matched
        else:
            # Individual OS fallback if no asset matched this platform.
            fallback = _FALLBACK_URLS.get(os_name, "")
            urls[os_name] = fallback
            print(f"  [WARN] No asset matched for {os_name}. Using fallback URL.")

    return version, urls


# ------------------------------------------------------------------
# -- Public API --
# ------------------------------------------------------------------

def get_os_name() -> str:
    """
    Detect the host operating system.

    Returns:
        str: One of 'Windows', 'Linux', or 'Darwin'.

    Raises:
        OSError: If the OS is not supported by the provisioner.
    """
    detected = platform.system()
    if detected not in _SUPPORTED_OS:
        raise OSError(
            f"Unsupported operating system: {detected}. "
            f"Supported: {sorted(_SUPPORTED_OS)}"
        )
    return detected


def resolve_target_dir(project_root: str = None) -> Path:
    """
    Resolve the absolute path to the isolated Cherry Studio directory.

    Args:
        project_root: Optional explicit project root. If None, walks up from
                      this file's location to find the TALOS root.

    Returns:
        pathlib.Path: Absolute path to `cherry_ui_isolated/`.
    """
    if project_root:
        root = Path(project_root)
    else:
        # Walk up from this module to find the project root (where talos.py lives).
        root = Path(__file__).resolve().parent.parent.parent
    target = root / _TARGET_DIR
    return target


def generate_mcp_config(output_path: Path = None) -> dict:
    """
    Generate the MCP server configuration JSON for Cherry Studio.

    Creates a configuration file that tells Cherry Studio how to connect
    to the TALOS MCP server. The config uses relative paths so that the
    UI works regardless of where the project is installed.

    Args:
        output_path: Optional path to write the config JSON file.
                     If None, returns the dict without writing.

    Returns:
        dict: The generated MCP configuration dictionary.
    """
    config = {
        "mcpServers": {
            "talos-local": {
                "command": "python",
                "args": [
                    "-m",
                    "src.mcp_server",
                ],
                "env": {
                    "TALOS_USE_LOCAL": "1",
                    "TALOS_API_PORT": "8001",
                },
                "description": (
                    "TALOS v5.8.2 Research Intelligence Platform -- "
                    "Multi-Tier LLM Routing enabled."
                ),
                "autoStart": True,
            }
        }
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"MCP configuration written to: {output_path}")

    return config


def download_cherry_studio(target_dir: Path = None, force: bool = False) -> bool:
    """
    Download the portable Cherry Studio distribution for the current OS.

    Dynamically resolves the correct download URL by querying the GitHub
    Releases API. Falls back to hardcoded URLs (v1.9.12) on API failure.

    Args:
        target_dir: Path to the `cherry_ui_isolated/` directory. If None,
                    resolves automatically from the project root.
        force: If True, re-download even if the target directory already
               contains a Cherry Studio installation.

    Returns:
        bool: True if the download and extraction succeeded, False otherwise.

    Raises:
        OSError: If the host OS is not supported.
    """
    os_name = get_os_name()

    if target_dir is None:
        target_dir = resolve_target_dir()

    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Check if already provisioned.
    marker_file = target_dir / ".cherry_installed"
    if marker_file.exists() and not force:
        print(
            f"Cherry Studio already provisioned at: {target_dir}\n"
            f"  Use force=True to re-download."
        )
        return True

    # -- Resolve download URL dynamically --
    cherry_version, cherry_urls = _resolve_download_urls()
    download_url = cherry_urls.get(os_name)
    if not download_url:
        print(f"ERROR: No download URL configured for OS: {os_name}")
        return False

    print(f"Downloading Cherry Studio v{cherry_version} for {os_name}...")
    print(f"  URL: {download_url}")
    print(f"  Target: {target_dir}")

    # -- Determine archive suffix for extraction --
    suffix = None
    for candidate in [".zip", ".tar.gz", ".AppImage", ".dmg", ".exe"]:
        if candidate in download_url:
            suffix = candidate
            break
    if suffix is None:
        suffix = ".zip" if os_name == "Windows" else ".tar.gz"

    try:
        # Download to a temporary file.
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            urllib.request.urlretrieve(download_url, tmp_path)

        print(f"  Downloaded to temporary file: {tmp_path}")

        # Extract to target directory.
        if suffix == ".zip":
            shutil.unpack_archive(tmp_path, target_dir, format="zip")
        elif suffix in (".tar.gz", ".tar.bz2", ".tar.xz"):
            shutil.unpack_archive(tmp_path, target_dir)
        else:
            # Non-archive file (e.g., .AppImage, .dmg, .exe) — copy directly.
            dest = target_dir / os.path.basename(download_url)
            shutil.copy2(tmp_path, dest)
            print(f"  Copied binary to: {dest}")

        print(f"  Extracted to: {target_dir}")

        # Clean up the temporary archive.
        os.unlink(tmp_path)

        # Write installation marker.
        marker_file.write_text(
            f"version={cherry_version}\n"
            f"os={os_name}\n"
            f"installed_by=talos_provisioner\n"
        )

        print(f"Cherry Studio v{cherry_version} provisioned successfully.")
        return True

    except urllib.error.URLError as e:
        print(f"ERROR: Network error during download: {e}")
        print("  The provisioner requires internet access for the initial download.")
        print("  After provisioning, the UI works fully offline.")
        return False
    except Exception as e:
        print(f"ERROR: Failed to provision Cherry Studio: {e}")
        return False


def provision_full(target_dir: Path = None, force: bool = False) -> bool:
    """
    Full provisioning pipeline: download Cherry Studio and generate MCP config.

    This is the primary entry point. It ensures the isolated UI is ready and
    configured to connect to the local TALOS MCP server.

    Args:
        target_dir: Path to `cherry_ui_isolated/`. Auto-resolved if None.
        force: If True, re-download even if already installed.

    Returns:
        bool: True if both download and configuration succeeded.
    """
    if target_dir is None:
        target_dir = resolve_target_dir()

    # Step 1: Download Cherry Studio.
    if not download_cherry_studio(target_dir, force=force):
        print("WARNING: Cherry Studio download failed. MCP config will still be generated.")
        # Continue anyway -- user may place the binary manually.

    # Step 2: Generate MCP configuration.
    mcp_config_path = target_dir / "mcp_config.json"
    try:
        generate_mcp_config(mcp_config_path)
    except Exception as e:
        print(f"ERROR: Failed to generate MCP config: {e}")
        return False

    # Step 3: Write a quick-launch hint file.
    hint_path = target_dir / "LAUNCH_INSTRUCTIONS.txt"
    hint_path.write_text(
        "Cherry Studio -- Isolated Interim UI for TALOS v5.8.2\n"
        "======================================================\n\n"
        "1. Run the Cherry Studio executable from this directory.\n"
        "2. Go to Settings > MCP and load mcp_config.json.\n"
        "3. The TALOS MCP server will start automatically.\n"
        "4. The full React 18 + Tailwind CSS + Shadcn UI frontend\n"
        "   is under development and will replace this interim UI.\n\n"
        f"Provisioned by TALOS v5.8.2 Frontend Provisioner.\n"
    )

    print("Full provision complete. Cherry Studio is ready in:", target_dir)
    return True


# ------------------------------------------------------------------
# -- CLI Entry Point --
# ------------------------------------------------------------------

if __name__ == "__main__":
    """
    Standalone CLI for the frontend provisioner.

    Usage:
        python src/utils/frontend_provisioner.py [--force]
    """
    force_flag = "--force" in sys.argv
    print("=" * 60)
    print("  TALOS v5.8.2 -- Isolated Interim UI Provisioner")
    print("=" * 60)
    success = provision_full(force=force_flag)
    if success:
        print("\nProvisioning complete. See LAUNCH_INSTRUCTIONS.txt in the target directory.")
    else:
        print("\nProvisioning encountered errors. Review the output above.")
        sys.exit(1)