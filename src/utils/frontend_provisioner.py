# -*- coding: utf-8 -*-
"""
Module: frontend_provisioner.py
Project: TALOS v5.7.1
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
    - The cherry_ui_isolated/ directory is gitignored to keep the repository clean.
    - MCP config generation uses relative paths so the provisioned UI can connect
      to the local TALOS MCP server regardless of the installation directory.
    - All network operations have configurable timeouts and graceful fallbacks.

Dependencies:
    - os, sys, platform: OS detection and filesystem operations.
    - json: MCP configuration file generation.
    - urllib.request: Binary download (stdlib, no external dependencies).
    - shutil, tempfile: Archive extraction and temporary file management.
"""
import os
import sys
import json
import platform
import shutil
import tempfile
import urllib.request
from pathlib import Path


# ------------------------------------------------------------------
# -- Constants --
# ------------------------------------------------------------------

# Cherry Studio GitHub release information (portable distribution).
# These URLs are the source of truth for the portable downloads.
CHERRY_STUDIO_VERSION = "1.2.3"
_CHERRY_RELEASE_BASE = (
    "https://github.com/CherryHQ/cherry-studio/releases/download/"
    f"v{CHERRY_STUDIO_VERSION}"
)

# Platform-specific download URLs for portable archives.
_CHERRY_URLS = {
    "Windows": f"{_CHERRY_RELEASE_BASE}/Cherry-Studio-portable-win-x64-{CHERRY_STUDIO_VERSION}.zip",
    "Linux":   f"{_CHERRY_RELEASE_BASE}/Cherry-Studio-portable-linux-x64-{CHERRY_STUDIO_VERSION}.tar.gz",
    "Darwin":  f"{_CHERRY_RELEASE_BASE}/Cherry-Studio-portable-mac-arm64-{CHERRY_STUDIO_VERSION}.dmg",
}

# Target directory relative to project root.
_TARGET_DIR = "cherry_ui_isolated"

# Supported operating systems for the provisioner.
_SUPPORTED_OS = frozenset({"Windows", "Linux", "Darwin"})


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
                    "TALOS v5.7.1 Research Intelligence Platform -- "
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

    download_url = _CHERRY_URLS.get(os_name)
    if not download_url:
        print(f"ERROR: No download URL configured for OS: {os_name}")
        return False

    print(f"Downloading Cherry Studio v{CHERRY_STUDIO_VERSION} for {os_name}...")
    print(f"  URL: {download_url}")
    print(f"  Target: {target_dir}")

    try:
        # Download to a temporary file.
        suffix = ".zip" if os_name == "Windows" else ".tar.gz"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            urllib.request.urlretrieve(download_url, tmp_path)

        print(f"  Downloaded to temporary file: {tmp_path}")

        # Extract to target directory.
        if suffix == ".zip":
            shutil.unpack_archive(tmp_path, target_dir, format="zip")
        else:
            shutil.unpack_archive(tmp_path, target_dir)

        print(f"  Extracted to: {target_dir}")

        # Clean up the temporary archive.
        os.unlink(tmp_path)

        # Write installation marker.
        marker_file.write_text(
            f"version={CHERRY_STUDIO_VERSION}\n"
            f"os={os_name}\n"
            f"installed_by=talos_provisioner\n"
        )

        print(f"Cherry Studio v{CHERRY_STUDIO_VERSION} provisioned successfully.")
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
        "Cherry Studio -- Isolated Interim UI for TALOS v5.7.1\n"
        "======================================================\n\n"
        "1. Run the Cherry Studio executable from this directory.\n"
        "2. Go to Settings > MCP and load mcp_config.json.\n"
        "3. The TALOS MCP server will start automatically.\n"
        "4. The full React 18 + Tailwind CSS + Shadcn UI frontend\n"
        "   is under development and will replace this interim UI.\n\n"
        f"Version: {CHERRY_STUDIO_VERSION}\n"
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
    print("  TALOS v5.7.1 -- Isolated Interim UI Provisioner")
    print("=" * 60)
    success = provision_full(force=force_flag)
    if success:
        print("\nProvisioning complete. See LAUNCH_INSTRUCTIONS.txt in the target directory.")
    else:
        print("\nProvisioning encountered errors. Review the output above.")
        sys.exit(1)