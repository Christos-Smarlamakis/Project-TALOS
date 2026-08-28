# -*- coding: utf-8 -*-
"""
Module: tray_icon.py
Project: TALOS v5.10.13
Description:
    Desktop Control Hub system tray companion for the TALOS autonomous research
    daemon. It renders a 16x16 navy/cyan icon and exposes a seven-item context
    menu that doubles as a self-healing control surface: open the 3D visualizer,
    open the reports folder, open the system log, open the Swagger API docs,
    trigger an instant search cycle, toggle console visibility, and terminate
    the daemon.

    The visualizer, Swagger docs, and instant-search actions self-heal the
    FastAPI backend first: they probe http://127.0.0.1:8001/api/v1/health and,
    when the server is offline, spawn the uvicorn app in a hidden background
    process (CREATE_NO_WINDOW on Windows) before opening the target URL.

    Heavy imports (pystray, Pillow) are lazy so the module stays importable in
    environments where those packages are not present. The tray loop runs in a
    non-blocking daemon thread so the caller (talos_service.py) can keep
    driving its main loop without being blocked.

Dependencies:
    - pystray (optional, lazy): system tray icon and context menu.
    - Pillow (optional, lazy): programmatic icon image generation.
    - urllib.request: HTTP liveness probe (standard library, no dependency).
    - requests (optional, lazy): non-blocking instant-search trigger POST.
    - ctypes, subprocess, threading, webbrowser, os, sys, time: OS integration.
"""
import os
import subprocess
import sys
import threading
import time
import webbrowser

# -- Canonical color constants for the programmatic tray icon --
DARK_NAVY = (0, 40, 85)      # #002855 -- TALOS brand navy
CYAN = (0, 206, 209)         # #00ced1 -- TALOS brand cyan

# -- Canonical FastAPI endpoints served on port 8001 --
API_BASE_URL = "http://127.0.0.1:8001"
HEALTH_URL = API_BASE_URL + "/api/v1/health"
VISUALIZER_URL = API_BASE_URL + "/api/v1/visualizer/live"
SWAGGER_URL = API_BASE_URL + "/docs"
SCRAPE_TRIGGER_URL = API_BASE_URL + "/api/v1/scrape/trigger"

# -- Canonical tray tooltip title --
TRAY_TITLE = "TALOS v5.10.13 | Research Intelligence Mesh"


def _project_root():
    """Resolve the project root by walking up until talos.py is found.

    Uses the same pattern as every other src/*.py module in the project so
    the tray helper is robust regardless of the current working directory.

    Returns:
        str: Absolute path to the project root directory.
    """
    root = os.path.abspath(os.path.dirname(__file__))
    while root and not os.path.exists(os.path.join(root, "talos.py")):
        parent = os.path.dirname(root)
        if parent == root:
            return os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )
        root = parent
    return root


def _open_path(path):
    """Open a filesystem path with the OS default handler.

    Args:
        path (str): Filesystem path to a file or directory.
    """
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def _is_api_alive(port=8001):
    """Probe the TALOS FastAPI health endpoint for liveness.

    Args:
        port (int): FastAPI server port (default 8001).

    Returns:
        bool: True when GET /api/v1/health returns HTTP 200 within 0.6s.
    """
    try:
        import urllib.request
        with urllib.request.urlopen(
            "http://127.0.0.1:{}/api/v1/health".format(port), timeout=0.6
        ) as response:
            return response.status == 200
    except Exception:
        return False


def _ensure_api_server():
    """Self-heal the TALOS FastAPI backend when it is offline.

    When the health probe reports the server is down, locate the project root
    and spawn ``uvicorn src.api.main_api:app`` in a hidden background process
    (CREATE_NO_WINDOW on Windows), then poll the health endpoint until it is
    responsive (up to 3 seconds).

    Returns:
        bool: True when the server is reachable after the attempt.
    """
    if _is_api_alive():
        return True

    root = _project_root()
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.main_api:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8001",
    ]
    kwargs = {
        "cwd": root,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        subprocess.Popen(command, **kwargs)
    except Exception:
        return False

    deadline = time.time() + 3.0
    while time.time() < deadline:
        if _is_api_alive():
            return True
        time.sleep(0.25)
    return False


def _build_tray_icon_image():
    """Generate a 16x16 navy/cyan tray icon via Pillow.

    Draws a stylized capital "T" (top bar plus vertical stem) in cyan over a
    dark navy background. Pillow is imported lazily so the module imports
    cleanly when Pillow is unavailable.

    Returns:
        PIL.Image.Image: The generated icon image.
    """
    from PIL import Image, ImageDraw

    size = 16
    image = Image.new("RGB", (size, size), DARK_NAVY)
    draw = ImageDraw.Draw(image)
    # -- Top horizontal bar of the "T" --
    draw.rectangle([2, 2, 13, 4], fill=CYAN)
    # -- Vertical stem of the "T" --
    draw.rectangle([7, 2, 9, 13], fill=CYAN)
    return image


def _get_console_window_handle():
    """Return the current process console window handle, or 0 when unknown.

    Returns:
        int: The HWND of the console window, or 0 when unavailable.
    """
    try:
        import ctypes
        return ctypes.windll.kernel32.GetConsoleWindow()
    except Exception:
        return 0


def _toggle_console_visibility():
    """Toggle the daemon console window between hidden and visible.

    Uses the Win32 ShowWindow API. SW_HIDE (0) and SW_SHOW (5) are applied
    alternately based on the window's current visibility.
    """
    try:
        import ctypes
        hwnd = _get_console_window_handle()
        if not hwnd:
            return
        user32 = ctypes.windll.user32
        # -- SW_HIDE = 0, SW_SHOW = 5 --
        if user32.IsWindowVisible(hwnd):
            user32.ShowWindow(hwnd, 0)
        else:
            user32.ShowWindow(hwnd, 5)
    except Exception:
        pass


def launch_tray_icon_async(on_show_hide=None, on_open_visualizer=None,
                           on_exit=None):
    """Launch the TALOS Desktop Control Hub tray icon in a daemon thread.

    Args:
        on_show_hide (callable, optional): Invoked for the Show / Hide Console
            Window menu item; defaults to the built-in Win32 console toggle.
        on_open_visualizer (callable, optional): Invoked for the Open 3D
            Visualizer menu item; defaults to self-healing bootstrap plus open.
        on_exit (callable, optional): Invoked for the Terminate Daemon menu
            item; the icon is stopped after the callback returns.

    Returns:
        threading.Thread | None: The background thread, or None when the tray
            icon could not be started (pystray/Pillow missing, or a non-GUI
            session). The caller is free to ignore the returned handle.
    """
    try:
        import pystray
    except ImportError:
        return None

    try:
        image = _build_tray_icon_image()
    except Exception:
        return None

    def _open_visualizer(icon, item):
        if callable(on_open_visualizer):
            on_open_visualizer()
            return
        if _ensure_api_server():
            webbrowser.open(VISUALIZER_URL)

    def _open_reports_folder(icon, item):
        root = _project_root()
        _open_path(os.path.join(root, "data", "reports"))

    def _open_system_log(icon, item):
        root = _project_root()
        _open_path(os.path.join(root, "data", "logs", "talos_system.log"))

    def _open_swagger(icon, item):
        if _ensure_api_server():
            webbrowser.open(SWAGGER_URL)

    def _trigger_search(icon, item):
        def _send():
            try:
                import requests
                if _ensure_api_server():
                    requests.post(SCRAPE_TRIGGER_URL, json={}, timeout=1.0)
            except Exception:
                pass
        threading.Thread(target=_send, name="talos-tray-search", daemon=True).start()

    def _toggle_console(icon, item):
        if callable(on_show_hide):
            on_show_hide()
        else:
            _toggle_console_visibility()

    def _terminate_daemon(icon, item):
        if callable(on_exit):
            on_exit()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Open 3D Visualizer", _open_visualizer),
        pystray.MenuItem("Open Reports Folder", _open_reports_folder),
        pystray.MenuItem("Open System Log", _open_system_log),
        pystray.MenuItem("Open API Docs (Swagger)", _open_swagger),
        pystray.MenuItem("Trigger Instant Search Cycle", _trigger_search),
        pystray.MenuItem("Show / Hide Console Window", _toggle_console),
        pystray.MenuItem("Terminate Daemon", _terminate_daemon),
    )

    icon = pystray.Icon(
        "talos", image, TRAY_TITLE, menu
    )

    def _run():
        try:
            icon.run()
        except Exception:
            pass

    thread = threading.Thread(target=_run, name="talos-tray-icon", daemon=True)
    thread.start()
    return thread
