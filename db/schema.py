"""Nuke Asset Browser — PostgreSQL schema & table initialisation.

All DDL is written to be **idempotent** — running ``ensure_schema()``
multiple times is safe.

Usage::

    from asset_browser.db.schema import ensure_schema
    ensure_schema()  # returns True / False

Or from the command line::

    python -m asset_browser.db.schema
"""

from __future__ import annotations

from asset_browser.db.connection import pg_pool
from asset_browser.utils.logger import get_logger

logger = get_logger(__name__)

# ── SQL ─────────────────────────────────────────────────────────────────

_CREATE_SCHEMA = """
    CREATE SCHEMA IF NOT EXISTS browser
        AUTHORIZATION CURRENT_USER;
"""

_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS browser.drafts (
        id                SERIAL PRIMARY KEY,
        name              TEXT NOT NULL,
        draft_type        TEXT NOT NULL DEFAULT 'other',
        path              TEXT NOT NULL DEFAULT '',
        author            TEXT NOT NULL DEFAULT 'artist',
        status            TEXT NOT NULL DEFAULT 'draft',
        visibility        TEXT NOT NULL DEFAULT 'private',
        favorite          BOOLEAN NOT NULL DEFAULT FALSE,
        description       TEXT NOT NULL DEFAULT '',
        tags              TEXT[] NOT NULL DEFAULT '{}',
        created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        thumbnail_path    TEXT NOT NULL DEFAULT '',
        use_count         INTEGER NOT NULL DEFAULT 0,
        frame_range       TEXT NOT NULL DEFAULT '',
        sequence_pattern  TEXT NOT NULL DEFAULT ''
    );
"""

_CREATE_INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS idx_drafts_author
        ON browser.drafts (author);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_drafts_type
        ON browser.drafts (draft_type);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_drafts_status
        ON browser.drafts (status);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_drafts_favorite
        ON browser.drafts (favorite)
        WHERE favorite = TRUE;
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_drafts_created
        ON browser.drafts (created_at DESC);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_drafts_updated
        ON browser.drafts (updated_at DESC);
    """,
    # GIN index for array-typed tags
    """
    CREATE INDEX IF NOT EXISTS idx_drafts_tags
        ON browser.drafts USING GIN (tags);
    """,
]

# ── Migration (v1 → v2: add sequence fields) ───────────────────────────

_MIGRATE_V1_V2 = [
    """
    ALTER TABLE browser.drafts
        ADD COLUMN IF NOT EXISTS frame_range TEXT NOT NULL DEFAULT '';
    """,
    """
    ALTER TABLE browser.drafts
        ADD COLUMN IF NOT EXISTS sequence_pattern TEXT NOT NULL DEFAULT '';
    """,
]


# ── Public API ──────────────────────────────────────────────────────────

def ensure_schema() -> bool:
    """Create the ``browser`` schema and ``browser.drafts`` table if they
    don't already exist.

    Returns:
        ``True`` if the schema is ready, ``False`` if the PG pool is
        unavailable or an error occurred.
    """
    if not pg_pool.ensure_connected():
        logger.warning("PG unavailable — cannot create schema")
        return False

    logger.info("Ensuring browser.drafts schema…")

    # Schema
    rc = pg_pool.execute(_CREATE_SCHEMA)
    if rc < 0:
        logger.error("Failed to create browser schema")
        return False

    # Table
    rc = pg_pool.execute(_CREATE_TABLE)
    if rc < 0:
        logger.error("Failed to create browser.drafts table")
        return False

    # Indexes
    for sql in _CREATE_INDEXES:
        pg_pool.execute(sql)

    # Migration: ensure all columns exist
    for sql in _MIGRATE_V1_V2:
        pg_pool.execute(sql)

    logger.info("browser.drafts schema ready")
    return True


# ── CLI entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    ok = ensure_schema()
    sys.exit(0 if ok else 1)
