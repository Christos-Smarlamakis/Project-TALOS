# -*- coding: utf-8 -*-
"""
Module: desktop_shortcut.py
Project: TALOS v5.18.2
Description:
    1-click Desktop Shortcut provisioner for Project TALOS. Resolves the
    operator's Windows Desktop directory and materializes a
    ``TALOS Research Hub.lnk`` launcher that targets ``run_talos.bat`` with the
    project root as its working directory. The shortcut is created through a
    zero-dependency PowerShell ``WScript.Shell`` COM dispatch, so no pywin32
    package is required and the provisioner works in a fresh conda environment.

    Key design decisions:
    - The Desktop path resolves through ``USERPROFILE\\Desktop`` with a
      OneDrive-redirected fallback (the modern Windows default).
    - The icon points at ``templates/assets/talos_icon.ico`` when present and
      otherwise falls back to a system icon (shell32.dll), so the provisioner
      never fails on a missing asset.
    - A Rich panel renders the confirmation (or a clear warning) so the
      operator receives unambiguous feedback from both the ``--create-shortcut``
      CLI flag and the Configuration & Profiles menu entry.

Dependencies:
    - os, subprocess: filesystem resolution and PowerShell COM dispatch.
    - rich (optional, lazy): confirmation panel rendering.
"""
import os
import subprocess

SHORTCUT_NAME = "TALOS Research Hub"
SHORTCUT_DESCRIPTION = "Project TALOS - Autonomous Research Intelligence Platform"


def _project_root():
    """Resolve the absolute project root by walking up until talos.py is found.

    Returns:
        str: Absolute path to the project root directory.
    """
    root = os.path.abspath(os.path.dirname(__file__))
    while root and not os.path.exists(os.path.join(root, "talos.py")):
        parent = os.path.dirname(root)
        if parent == root:
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        root = parent
    return root


def _desktop_dir():
    """Resolve the operator's Windows Desktop directory (OneDrive-aware).

    Returns:
        str: Absolute path to the best available Desktop directory.
    """
    userprofile = os.environ.get("USERPROFILE", "")
    candidates = []
    if userprofile:
        candidates.append(os.path.join(userprofile, "Desktop"))
        candidates.append(os.path.join(userprofile, "OneDrive", "Desktop"))
    candidates.append(os.path.expanduser("~/Desktop"))
    for path in candidates:
        if path and os.path.isdir(path):
            return path
    return candidates[0] if candidates else os.path.expanduser("~/Desktop")


def _icon_location(root):
    """Return the icon spec for the shortcut, falling back to a system icon.

    Args:
        root (str): Absolute project root directory.

    Returns:
        str: An ``.ico`` path or a ``shell32.dll,<index>`` spec.
    """
    icon_path = os.path.join(root, "templates", "assets", "talos_icon.ico")
    if os.path.exists(icon_path):
        return icon_path
    return "shell32.dll, 13"


def create_desktop_shortcut():
    """Create (or refresh) the TALOS Research Hub desktop shortcut.

    Returns:
        bool: True when the shortcut was created successfully, False otherwise.
    """
    root = _project_root()
    desktop = _desktop_dir()
    target = os.path.join(root, "run_talos.bat")
    shortcut_path = os.path.join(desktop, SHORTCUT_NAME + ".lnk")
    icon = _icon_location(root)

    if not os.path.exists(target):
        _render_result(False, shortcut_path, "run_talos.bat not found at " + target)
        return False

    # -- PowerShell WScript.Shell COM dispatch (zero external dependency). --
    ps_script = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{shortcut}'); "
        "$s.TargetPath = '{target}'; "
        "$s.WorkingDirectory = '{workdir}'; "
        "$s.Description = '{description}'; "
        "$s.IconLocation = '{icon}'; "
        "$s.Save()"
    ).format(
        shortcut=shortcut_path.replace("'", "''"),
        target=target.replace("'", "''"),
        workdir=root.replace("'", "''"),
        description=SHORTCUT_DESCRIPTION.replace("'", "''"),
        icon=icon.replace("'", "''"),
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception as exc:
        _render_result(False, shortcut_path, "PowerShell dispatch failed: {}".format(exc))
        return False

    ok = result.returncode == 0 and os.path.exists(shortcut_path)
    _render_result(ok, shortcut_path, (result.stderr or "").strip())
    return ok


def _render_result(success, shortcut_path, detail):
    """Render a Rich confirmation or warning panel for the shortcut result.

    Args:
        success (bool): Whether the shortcut was created.
        shortcut_path (str): Target .lnk path.
        detail (str): Additional diagnostic text on failure.
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        if success:
            console.print(Panel(
                "[bold green]Success:[/bold green] Desktop shortcut created at {path}".format(
                    path=shortcut_path),
                title="TALOS Desktop Provisioner",
                border_style="green",
            ))
        else:
            console.print(Panel(
                "[yellow]Desktop shortcut not created.[/yellow]\n{detail}".format(
                    detail=detail or ""),
                title="TALOS Desktop Provisioner",
                border_style="yellow",
            ))
    except Exception:
        if success:
            print("[OK] Desktop shortcut created at {}".format(shortcut_path))
        else:
            print("[WARN] Desktop shortcut not created: {}".format(detail))


if __name__ == "__main__":
    import sys
    sys.exit(0 if create_desktop_shortcut() else 1)
