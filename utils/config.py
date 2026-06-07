"""Nuke Asset Browser — Configuration Manager

读取优先级:
  1. 环境变量 (前缀 AM_)
  2. YAML 配置文件 (~/.config/asset_browser/config.yaml)
  3. 代码内默认值

Usage:
    from asset_browser.utils.config import config
    print(config.user_name)
    print(config.pg_host)
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from typing import Optional


# ── Defaults ─────────────────────────────────────────────────────────────
_DEFAULT_CONFIG = {
    # User
    "user_name": os.environ.get("USER", os.environ.get("USERNAME", "artist")),

    # Templates / drafts
    "template_dir": os.path.join(
        os.path.expanduser("~"), ".nuke", "AssetBrowser", "templates"
    ),
    # Thumbnail
    "thumbnail_size": [260, 180],
    "thumbnail_cache_dir": os.path.join(
        os.environ.get("HOME", os.path.expanduser("~")),
        ".nuke", "AssetBrowser", "thumbnails"
    ),

    # Cache
    "json_cache_path": os.path.join(
        os.path.expanduser("~"), ".cache", "asset_browser"
    ),

    # PostgreSQL
    "pg_host": "localhost",
    "pg_port": 5432,
    "pg_database": "pipeline_db",
    "pg_user": "",
    "pg_password": "",
}

_ENV_PREFIX = "AM_"


def _load_config_file() -> dict:
    """Load user config from ~/.config/asset_browser/config.yaml (or .json).

    Returns empty dict if file doesn't exist.
    """
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "asset_browser")
    yaml_path = os.path.join(config_dir, "config.yaml")
    json_path = os.path.join(config_dir, "config.json")

    if os.path.isfile(yaml_path):
        try:
            import yaml
            with open(yaml_path, "r") as f:
                return yaml.safe_load(f) or {}
        except (ImportError, Exception):
            pass  # fall through

    if os.path.isfile(json_path):
        try:
            with open(json_path, "r") as f:
                return json.load(f) or {}
        except Exception:
            pass

    return {}


def _env_key(key: str) -> str:
    """Convert config key to environment variable name.

    E.g. ``pg_host`` → ``AM_PG_HOST``
    """
    return _ENV_PREFIX + key.upper()


def _resolve(key: str, file_cfg: dict) -> str | int | list:
    """Resolve a single config value: env var > file > default."""
    env_val = os.environ.get(_env_key(key))
    if env_val is not None:
        # Attempt type-coercion to match default's type
        default = _DEFAULT_CONFIG.get(key)
        if isinstance(default, int):
            try:
                return int(env_val)
            except ValueError:
                return env_val
        if isinstance(default, list):
            try:
                return json.loads(env_val)
            except (json.JSONDecodeError, TypeError):
                return env_val
        return env_val

    if key in file_cfg:
        return file_cfg[key]

    return _DEFAULT_CONFIG.get(key)


class Config:
    """Application-wide configuration (singleton-like accessor).

    All attributes are resolved lazily from environment variables,
    the user config file, or built-in defaults.
    """

    def __init__(self):
        self._file_cfg = _load_config_file()

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def user_name(self) -> str:
        """Current user display name."""
        return _resolve("user_name", self._file_cfg)  # type: ignore[return-value]

    @property
    def thumbnail_size(self) -> list[int]:
        """Thumbnail dimensions [width, height]."""
        return list(_resolve("thumbnail_size", self._file_cfg))  # type: ignore[arg-type]

    @property
    def thumbnail_cache_dir(self) -> str:
        """Directory where generated thumbnail images are cached."""
        return _resolve("thumbnail_cache_dir", self._file_cfg)  # type: ignore[return-value]

    @property
    def json_cache_path(self) -> str:
        """Directory for JSON cache / offline fallback storage."""
        return _resolve("json_cache_path", self._file_cfg)  # type: ignore[return-value]

    @property
    def template_dir(self) -> str:
        """Persistent directory for exported .nk templates.

        Controlled by env var ``AM_TEMPLATE_DIR``.
        Defaults to ``~/.nuke/AssetBrowser/templates/``.
        """
        return _resolve("template_dir", self._file_cfg)  # type: ignore[return-value]

    @property
    def pg_host(self) -> str:
        """PostgreSQL host."""
        return _resolve("pg_host", self._file_cfg)  # type: ignore[return-value]

    @property
    def pg_port(self) -> int:
        """PostgreSQL port."""
        return int(_resolve("pg_port", self._file_cfg))  # type: ignore[return-value]

    @property
    def pg_database(self) -> str:
        """PostgreSQL database name."""
        return _resolve("pg_database", self._file_cfg)  # type: ignore[return-value]

    @property
    def pg_user(self) -> str:
        """PostgreSQL user."""
        return _resolve("pg_user", self._file_cfg)  # type: ignore[return-value]

    @property
    def pg_password(self) -> str:
        """PostgreSQL password."""
        return _resolve("pg_password", self._file_cfg)  # type: ignore[return-value]

    # ── Convenience ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Dump all resolved config values as a flat dict."""
        return {k: _resolve(k, self._file_cfg) for k in _DEFAULT_CONFIG}


# ── Module-level singleton ───────────────────────────────────────────────
config = Config()
