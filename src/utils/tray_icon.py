# -*- coding: utf-8 -*-
"""
Module: tray_icon.py
Project: TALOS v5.10.12
Description:
    Windows system tray companion for the TALOS autonomous research daemon.
    It renders a 16x16 navy/cyan icon and exposes a three-item context menu:
    open the 3D visualizer, toggle console window visibility, and terminate
    the daemon. Heavy imports (pystray, Pillow) are lazy so the module stays
    importable in environments where those packages are not present.

    The tray loop runs in a non-blocking daemon thread, so the caller
    (talos_service.py) can keep driving its main loop without being blocked.

Dependencies:
    - pystray (optional, lazy): system tray icon and context menu.
    - Pillow (optional, lazy): programmatic icon image generation.
    - ctypes, threading, webbrowser: standard library integration.
"""
import threading
import webbrowser

# -- Canonical color constants for the programmatic tray icon --
DARK_NAVY = (0, 40, 85)      # #002855 -- TALOS brand navy
CYAN = (0, 206, 209)         # #00ced1 -- TALOS brand cyan

# -- Canonical visualizer URL served by FastAPI on port 8001 --
VISUALIZER_URL = "http://127.0.0.1:8001/api/v1/visualizer/live"


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
    """Launch the TALOS system tray icon in a non-blocking daemon thread.

    Args:
        on_show_hide (callable, optional): Invoked for the Show / Hide Console
            menu item; defaults to the built-in Win32 console visibility toggle.
        on_open_visualizer (callable, optional): Invoked for the Open 3D
            Visualizer menu item; defaults to opening the visualizer URL.
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
        else:
            webbrowser.open(VISUALIZER_URL)

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
        pystray.MenuItem("Show / Hide Console", _toggle_console),
        pystray.MenuItem("Terminate Daemon", _terminate_daemon),
    )

    icon = pystray.Icon(
        "talos", image, "TALOS Autonomous Research Daemon", menu
    )

    def _run():
        try:
            icon.run()
        except Exception:
            pass

    thread = threading.Thread(target=_run, name="talos-tray-icon", daemon=True)
    thread.start()
    return thread
