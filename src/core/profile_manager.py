# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.

"""
Module: profile_manager.py
Project: TALOS v5.18.3
Description:
    Single Source of Truth (SSOT) for the TALOS multi-profile workspace. This
    module anchors every profile operation to the repository-root ``_profiles/``
    directory (derived via ``Path(__file__).resolve().parents[2]``), so profile
    resolution is independent of the current working directory and immune to the
    legacy relative-path bugs that previously produced phantom databases and
    stale active-profile markers.

    The canonical ``ProfileManager`` class exposes the complete profile state
    machine: directory discovery, active-profile marker I/O, profile listing,
    creation, and activation, plus two-direction config synchronization between
    the root working copy (``config.json``) and each isolated
    ``_profiles/<name>/`` workspace. A module-level singleton and thin function
    aliases preserve backward compatibility for ``talos.py`` and other callers.

    Key design decisions:
    - Repo-root anchoring: ``PROFILES_DIR = REPO_ROOT / "_profiles"``.
    - Active profile marker: ``_profiles/active_profile.txt`` (default
      ``"default"``).
    - Two-direction config sync: ``save_current_state_to_profile`` persists the
      root working copy into a profile, while ``set_active_profile`` loads the
      selected profile back into the root working copy.
    - Name validation: a single-path-component regex rejects separators, spaces,
      and empty names before any filesystem mutation.

Dependencies:
    - pathlib: Repo-root-relative path construction.
    - sqlite3: Creation of a fresh, valid per-profile database file.
    - questionary: Interactive profile management menu (subprocess entry point).
    - src.utils.ui_theme: Canonical TALOS prompt theme.
"""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

# -- Bootstrap the project root onto sys.path so this module can also run as a
# -- standalone subprocess (launched by talos.py via run_script). --
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P:
    sys.path.insert(0, _P)

# -- Repo-root anchored canonical locations (single source of truth). --
REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILES_DIR = REPO_ROOT / "_profiles"
ACTIVE_PROFILE_FILE = PROFILES_DIR / "active_profile.txt"
DEFAULT_PROFILE = "default"

# -- Profile names must resolve to a single safe path component. --
_PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]*$")


def _validate_profile_name(name):
    """Return True when ``name`` is a safe single path component."""
    return bool(name) and bool(_PROFILE_NAME_RE.match((name or "").strip()))


class ProfileManager:
    """Canonical multi-profile workspace manager (single source of truth).

    Attributes:
        root (Path): Repository root directory.
        profiles_dir (Path): Absolute ``_profiles`` directory.
        active_file (Path): Absolute ``active_profile.txt`` marker path.
    """

    def __init__(self, root=None):
        """Initialize the manager, optionally overriding the repository root.

        Args:
            root (str or Path, optional): Override for hermetic testing. When
                omitted, the repository root is derived from ``__file__``.
        """
        self.root = (Path(root).resolve() if root is not None else REPO_ROOT)
        self.profiles_dir = self.root / "_profiles"
        self.active_file = self.profiles_dir / "active_profile.txt"

    # -- Discovery --------------------------------------------------------
    def get_profiles_dir(self):
        """Return the absolute ``_profiles`` directory, creating it if needed.

        Returns:
            Path: Absolute path to the profiles directory.
        """
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        return self.profiles_dir

    def get_active_profile_name(self):
        """Read the active profile name from the marker file.

        Returns:
            str: Active profile name, defaulting to ``default`` when absent.
        """
        self.get_profiles_dir()
        if self.active_file.exists():
            try:
                name = self.active_file.read_text(encoding="utf-8").strip()
                if name:
                    return name
            except OSError:
                pass
        return DEFAULT_PROFILE

    def list_profiles(self):
        """Return a sorted list of valid profile directory names.

        Returns:
            list[str]: Sorted profile names (may be empty).
        """
        profiles_dir = self.get_profiles_dir()
        return sorted(p.name for p in profiles_dir.iterdir() if p.is_dir())

    # -- Config synchronization ------------------------------------------
    def _root_config_path(self):
        """Return the root config path, falling back to the template."""
        candidate = self.root / "config.json"
        if candidate.exists():
            return candidate
        return self.root / "config.template.json"

    def _load_profile_config_to_root(self, name):
        """Copy a profile's config.json into the root working copy."""
        src = self.profiles_dir / name / "config.json"
        if src.exists():
            shutil.copy2(str(src), str(self.root / "config.json"))

    def _persist_root_config_to_profile(self, name):
        """Persist the root config.json into the named profile."""
        profile_dir = self.profiles_dir / name
        profile_dir.mkdir(parents=True, exist_ok=True)
        src = self._root_config_path()
        if src.exists():
            shutil.copy2(str(src), str(profile_dir / "config.json"))

    # -- State machine ----------------------------------------------------
    def set_active_profile(self, name):
        """Validate, scaffold, and activate the named profile.

        Args:
            name (str): Target profile name.

        Returns:
            str: The activated profile name.

        Raises:
            ValueError: When ``name`` fails path-component validation.
        """
        if not _validate_profile_name(name):
            raise ValueError("Invalid profile name: {!r}".format(name))
        profile_dir = self.profiles_dir / name
        profile_dir.mkdir(parents=True, exist_ok=True)
        # Seed a config for brand-new profiles; otherwise load the profile's
        # persisted config into the root working copy (activation).
        if not (profile_dir / "config.json").exists():
            self._persist_root_config_to_profile(name)
        self.active_file.write_text(name, encoding="utf-8")
        self._load_profile_config_to_root(name)
        return name

    def create_profile(self, name, seed_config=None):
        """Scaffold a fresh isolated profile and activate it.

        Args:
            name (str): New profile name.
            seed_config (dict, optional): Initial config dict. When omitted the
                root config.json (or template) is copied as the seed.

        Returns:
            str: The newly created and activated profile name.
        """
        if not _validate_profile_name(name):
            raise ValueError("Invalid profile name: {!r}".format(name))
        profile_dir = self.profiles_dir / name
        profile_dir.mkdir(parents=True, exist_ok=True)

        # -- Config --
        config_path = profile_dir / "config.json"
        if seed_config is not None:
            config_path.write_text(
                json.dumps(seed_config, indent=2, ensure_ascii=False),
                encoding="utf-8")
        elif not config_path.exists():
            src = self._root_config_path()
            shutil.copy2(str(src), str(config_path))

        # -- Fresh database (a valid empty SQLite file; the schema is created
        # -- lazily by DatabaseManager on first use). --
        db_path = profile_dir / "talos_research.db"
        if not db_path.exists():
            sqlite3.connect(str(db_path)).close()

        return self.set_active_profile(name)

    def get_active_db_path(self):
        """Return the absolute path to the active profile's database.

        Returns:
            str: ``_profiles/<active>/talos_research.db``.
        """
        name = self.get_active_profile_name()
        profile_dir = self.profiles_dir / name
        profile_dir.mkdir(parents=True, exist_ok=True)
        return str(profile_dir / "talos_research.db")

    def get_active_config_path(self):
        """Return the absolute path to the active profile's config.json.

        Returns:
            str: ``_profiles/<active>/config.json``.
        """
        name = self.get_active_profile_name()
        return str(self.profiles_dir / name / "config.json")


# -- Module-level singleton (used by all delegating consumers). --
_profile_manager = ProfileManager()


# ---------------------------------------------------------------------------
# -- Backward-compatible module-level aliases --
# ---------------------------------------------------------------------------

def ensure_profiles_dir():
    """Create the profiles directory if it does not yet exist."""
    return _profile_manager.get_profiles_dir()


def get_active_profile_name():
    """Return the active profile name (module-level alias)."""
    return _profile_manager.get_active_profile_name()


def set_active_profile_name(name):
    """Persist and activate the profile name (module-level alias)."""
    return _profile_manager.set_active_profile(name)


def save_current_state_to_profile(profile_name):
    """Persist the root working copy into the named profile."""
    return _profile_manager._persist_root_config_to_profile(profile_name)


def load_profile_to_root(profile_name):
    """Load the named profile's config back into the root working copy."""
    return _profile_manager._load_profile_config_to_root(profile_name)


def run_pythia_script():
    """Run the PYTHIA query-translator script as a subprocess.

    Returns:
        bool: True when the subprocess completes successfully, False otherwise.
    """
    python_exe = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "query_translator.py")
    print("\n--- Starting PYTHIA (research goal configuration)... ---\n")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        subprocess.run([python_exe, script_path], check=True, env=env)
        return True
    except Exception as exc:
        print("Error running PYTHIA: {}".format(exc))
        return False


def create_new_profile():
    """Interactive wrapper for creating and configuring a new profile."""
    import questionary
    from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE
    name = questionary.text("New profile name:", style=TALOS_QUESTIONARY_STYLE).ask()
    if not name:
        return
    safe_name = (name or "").strip()
    if not _validate_profile_name(safe_name):
        print("Invalid profile name. Use only letters, digits, underscores, and hyphens.")
        return
    _profile_manager.create_profile(safe_name)
    print("\n--- New profile '{}' created. ---".format(safe_name))
    if questionary.confirm(
            "Configure the research goal (PYTHIA) now?",
            default=True, style=TALOS_QUESTIONARY_STYLE).ask():
        if run_pythia_script():
            print("\n[Saving] Saving new settings to profile...")
            save_current_state_to_profile(safe_name)


def switch_profile():
    """Interactive profile switcher."""
    import questionary
    from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE
    current = get_active_profile_name()
    profiles = _profile_manager.list_profiles()
    if not profiles:
        print("No saved profiles exist.")
        return
    if current not in profiles:
        profiles.append(current)
    choice = questionary.select(
        "Current Profile: [{}]. Select a profile to load:".format(current),
        choices=sorted(profiles) + ["Cancel"],
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if choice == "Cancel" or choice is None:
        return
    if choice == current:
        print("You are already using this profile.")
        return
    print("\n[Saving] Saving state of '{}'...".format(current))
    save_current_state_to_profile(current)
    print("\n[Loading] Loading profile '{}'...".format(choice))
    _profile_manager.set_active_profile(choice)


def configure_current_profile():
    """Run PYTHIA against the currently active profile."""
    import questionary
    from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE
    current = get_active_profile_name()
    if questionary.confirm(
            "WARNING: This will change the Queries/Prompts for profile '{}'. Continue?".format(current),
            default=False, style=TALOS_QUESTIONARY_STYLE).ask():
        if run_pythia_script():
            print("\n[Saving] Saving new settings to profile '{}'...".format(current))
            save_current_state_to_profile(current)


def main():
    """Interactive profile management menu (standalone subprocess entry)."""
    import questionary
    from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE
    if not ACTIVE_PROFILE_FILE.exists():
        set_active_profile_name(DEFAULT_PROFILE)
        save_current_state_to_profile(DEFAULT_PROFILE)

    current = get_active_profile_name()
    try:
        choice = questionary.select(
            "PROFILE MANAGEMENT | Active: [{}]".format(current),
            choices=[
                "1. Switch Profile",
                "2. Create New Profile (+ Auto Setup)",
                "3. PYTHIA Goal Configuration (Active Profile)",
                "4. Save Current State",
                questionary.Separator(),
                "Return",
            ],
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()
    except Exception:
        choice = questionary.select(
            "Options:",
            choices=["1. Switch", "2. Create", "3. Configure (PYTHIA)", "4. Save", "Return"],
            style=TALOS_QUESTIONARY_STYLE,
        ).unsafe_ask()

    if not choice or "Return" in choice:
        return
    if choice.startswith("1."):
        switch_profile()
    elif choice.startswith("2."):
        create_new_profile()
    elif choice.startswith("3."):
        configure_current_profile()
    elif choice.startswith("4."):
        save_current_state_to_profile(current)


if __name__ == "__main__":
    main()