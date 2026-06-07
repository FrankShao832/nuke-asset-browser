"""Nuke Asset Browser — Logging utilities

All Asset Browser modules should use ``get_logger(__name__)`` instead of
``print()``.  Log output goes to **stderr** with a consistent format.

Usage::

    from asset_browser.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Browser initialised")
    logger.debug(f"Loaded {n} drafts")
    logger.warning("PG connection unavailable, falling back to JSON")
"""

from __future__ import annotations

import logging
import os
import sys

# ── Constants ────────────────────────────────────────────────────────────

_LOG_FORMAT = "[%(levelname)s] %(asctime)s  %(name)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_DEFAULT_LEVEL = logging.INFO

# ── Module-level state ──────────────────────────────────────────────────

_handler: logging.Handler | None = None
_loggers: dict[str, logging.Logger] = {}


def _ensure_handler() -> logging.Handler:
    """Return the shared stderr handler, creating it on first call."""
    global _handler
    if _handler is None:
        _handler = logging.StreamHandler(sys.stderr)
        _handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    return _handler


def _resolve_level() -> int:
    """Resolve log level from env var ``AM_LOG_LEVEL``, defaulting to INFO.

    Returns:
        One of ``logging.DEBUG`` / ``INFO`` / ``WARNING`` / ``ERROR``.
    """
    raw = os.environ.get("AM_LOG_LEVEL", "INFO").upper()
    return _LEVEL_MAP.get(raw, _DEFAULT_LEVEL)


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """Get (or create) a named logger with the Asset Browser format.

    All loggers share a single stderr handler — no duplicate output.

    Args:
        name: Logger name — always pass ``__name__`` from the caller.
        level: Optional override.  If ``None``, reads from ``AM_LOG_LEVEL``
               env var or defaults to ``INFO``.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.addHandler(_ensure_handler())
    logger.setLevel(level if level is not None else _resolve_level())
    logger.propagate = False  # don't bubble to the root logger
    _loggers[name] = logger
    return logger


def set_level(level: int) -> None:
    """Globally change the log level for all Asset Browser loggers.

    Args:
        level: One of ``logging.DEBUG``, ``INFO``, ``WARNING``, ``ERROR``.
    """
    for logger in _loggers.values():
        logger.setLevel(level)
