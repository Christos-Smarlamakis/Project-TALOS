# -*- coding: utf-8 -*-
"""
Module: logger.py
Project: TALOS v5.10.0
Description:
    Enterprise logging configuration for TALOS. Provides a single
    get_logger(name) factory that attaches two primary handlers to a shared
    root logger: a rich.logging.RichHandler for structured, emoji-free console
    output, and a logging.handlers.RotatingFileHandler writing to
    data/logs/talos_system.log (10 MB per file, 5 rotating backups) with an
    explicit academic formatter.

    Key design decisions:
    - The data/logs/ directory is created automatically if it does not exist.
    - The root "talos" logger is configured exactly once; repeated calls to
      get_logger() are idempotent and never attach duplicate handlers.
    - The root logger disables propagation so TALOS records do not leak into
      third-party root handlers (for example, uvicorn).
    - The file handler uses %(asctime)s - %(name)s - %(levelname)s - %(message)s
      so that every line is self-describing and machine-parseable.

Dependencies:
    - logging, logging.handlers: Python standard library logging framework.
    - rich.logging.RichHandler: Colorized, structured console rendering.
    - pathlib.Path: Project-root resolution for the log directory.
"""
import logging
import logging.handlers
from pathlib import Path

# -- Project root resolution (src/utils/logger.py -> project root) ------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "data" / "logs"
_LOG_FILE = _LOG_DIR / "talos_system.log"

# -- Constants ----------------------------------------------------------------
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per rotating file
LOG_BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_ROOT_LOGGER_NAME = "talos"

_configured = False


def _configure() -> None:
    """Configure the root TALOS logger once; safe to call repeatedly."""
    global _configured
    if _configured:
        return

    # Ensure the log directory exists before attaching the file handler.
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger(_ROOT_LOGGER_NAME)
    root_logger.setLevel(logging.INFO)
    root_logger.propagate = False

    # -- Console handler: rich, colorized, emoji-free -------------------------
    from rich.logging import RichHandler

    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        show_path=False,
        markup=True,
    )
    console_handler.setLevel(logging.INFO)

    # -- File handler: rotating, academic formatter ---------------------------
    file_handler = logging.handlers.RotatingFileHandler(
        str(_LOG_FILE),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured child logger under the TALOS root logger.

    Args:
        name (str): Logger name, conventionally the module's __name__.

    Returns:
        logging.Logger: Logger instance sharing the TALOS console and file
        handlers configured by _configure().
    """
    _configure()
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
