"""Nuke Asset Browser — Storage backend auto-select & sync.

Auto-selects ``PGDraftStorage`` when PostgreSQL is available, falling
back to ``JSONDraftStorage`` otherwise.  Also provides a one-shot
sync function to migrate JSON data into PostgreSQL.

Usage::

    from asset_browser.db.sync import get_storage, force_storage, sync_to_pg

    store = get_storage()  # PGDraftStorage or JSONDraftStorage
    drafts = store.list_drafts()
"""

from __future__ import annotations

from typing import Optional

from asset_browser.db.base import DraftStorage
from asset_browser.db.connection import pg_pool
from asset_browser.db.json_store import JSONDraftStorage
from asset_browser.db.pg_store import PGDraftStorage
from asset_browser.db.schema import ensure_schema
from asset_browser.utils.logger import get_logger

logger = get_logger(__name__)

# ── Module-level state ──────────────────────────────────────────────────

_backend: str | None = None  # "pg", "json", or None (auto)
_storage: DraftStorage | None = None


# ── Public API ──────────────────────────────────────────────────────────

def get_storage() -> DraftStorage:
    """Return the most suitable draft storage backend.

    Priority:
    1. If ``force_storage()`` was called, use that backend.
    2. If PostgreSQL is reachable and the schema exists → ``PGDraftStorage``.
    3. Otherwise → ``JSONDraftStorage``.

    The decision is cached after the first successful connection attempt.
    Call ``force_storage(None)`` to reset and re-evaluate on the next call.
    """
    global _storage, _backend

    if _storage is not None:
        return _storage

    # Forced backend
    if _backend == "pg":
        _storage = _try_pg()
    elif _backend == "json":
        _storage = JSONDraftStorage()
    elif _backend is None:
        # Auto-detect
        _storage = _try_pg()
        if _storage is None:
            _storage = JSONDraftStorage()
            logger.info("Auto-selected: JSONDraftStorage")

    return _storage  # type: ignore[return-value]


def force_storage(backend: str | None) -> None:
    """Force a specific storage backend for subsequent ``get_storage()``
    calls.

    Args:
        backend: ``"pg"``, ``"json"``, or ``None`` to re-enable auto-detect.
    """
    global _storage, _backend
    _storage = None
    _backend = backend
    logger.info("Storage forced to: %s", backend or "auto")


def sync_to_pg() -> int:
    """Copy all drafts from JSON storage into PostgreSQL.

    Idempotent — drafts that already exist in PG (matched by id) are
    **updated** rather than re-inserted.

    Returns:
        Number of drafts synced, or ``-1`` if PG is unavailable.
    """
    if not pg_pool.ensure_connected():
        logger.warning("PG unavailable — cannot sync")
        return -1

    ensure_schema()

    json_store = JSONDraftStorage()
    pg_store = PGDraftStorage()
    drafts = json_store.list_drafts()

    if not drafts:
        logger.info("Nothing to sync — JSON store is empty")
        return 0

    synced = 0
    for draft in drafts:
        existing = pg_store.get_draft(draft.id)
        if existing:
            pg_store.update_draft(draft)
        else:
            # Reset id so SERIAL auto-assigns
            draft.id = 0
            pg_store.add_draft(draft)
        synced += 1

    logger.info("Synced %d drafts from JSON → PG", synced)
    return synced


# ── Internal helpers ────────────────────────────────────────────────────

def _try_pg() -> Optional[DraftStorage]:
    """Try to create a PGDraftStorage if PG is reachable and schema ready.

    Returns ``None`` (and logs a warning) on failure — never raises.
    """
    if not pg_pool.ensure_connected():
        logger.warning("PG unavailable — falling back to JSON")
        return None

    if not ensure_schema():
        logger.warning("PG schema not ready — falling back to JSON")
        return None

    logger.info("Auto-selected: PGDraftStorage")
    return PGDraftStorage()


# ── CLI entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if "--sync" in sys.argv:
        n = sync_to_pg()
        print(f"Synced {n} drafts")
        sys.exit(0 if n >= 0 else 1)
    elif "--force-pg" in sys.argv:
        force_storage("pg")
    elif "--force-json" in sys.argv:
        force_storage("json")

    store = get_storage()
    print(f"Backend: {type(store).__name__}")
    print(f"Drafts:  {len(store.list_drafts())}")
    pg_pool.disconnect()
