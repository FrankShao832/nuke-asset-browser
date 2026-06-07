"""Nuke Asset Browser — PostgreSQL draft storage implementation.

Implements :class:`~asset_browser.db.base.DraftStorage` against the
``browser.drafts`` table created by :mod:`~asset_browser.db.schema`.
"""

from __future__ import annotations

from typing import Optional

from asset_browser.core.models import Draft
from asset_browser.db.base import DraftStorage
from asset_browser.db.connection import pg_pool
from asset_browser.utils.logger import get_logger

logger = get_logger(__name__)

# ── SQL constants ───────────────────────────────────────────────────────

_SELECT_ALL = """
    SELECT * FROM browser.drafts ORDER BY id
"""

_SELECT_BY_ID = """
    SELECT * FROM browser.drafts WHERE id = %s
"""

_INSERT = """
    INSERT INTO browser.drafts
        (name, draft_type, path, author, status, visibility,
         favorite, description, tags, created_at, updated_at,
         thumbnail_path, use_count)
    VALUES
        (%(name)s, %(draft_type)s, %(path)s, %(author)s, %(status)s,
         %(visibility)s, %(favorite)s, %(description)s, %(tags)s,
         %(created_at)s, %(updated_at)s, %(thumbnail_path)s, %(use_count)s)
    RETURNING id
"""

_UPDATE = """
    UPDATE browser.drafts SET
        name          = %(name)s,
        draft_type    = %(draft_type)s,
        path          = %(path)s,
        author        = %(author)s,
        status        = %(status)s,
        visibility    = %(visibility)s,
        favorite      = %(favorite)s,
        description   = %(description)s,
        tags          = %(tags)s,
        created_at    = %(created_at)s,
        updated_at    = %(updated_at)s,
        thumbnail_path= %(thumbnail_path)s,
        use_count     = %(use_count)s
    WHERE id = %(id)s
"""

_DELETE = """
    DELETE FROM browser.drafts WHERE id = %s
"""


def _draft_to_params(draft: Draft) -> dict:
    """Convert a Draft dataclass to a parameter dict for SQL queries."""
    return {
        "id": draft.id,
        "name": draft.name,
        "draft_type": draft.draft_type,
        "path": draft.path,
        "author": draft.author,
        "status": draft.status,
        "visibility": draft.visibility,
        "favorite": draft.favorite,
        "description": draft.description,
        "tags": draft.tags,  # psycopg2 adapts list[str] → TEXT[]
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
        "thumbnail_path": draft.thumbnail_path,
        "use_count": draft.use_count,
    }


def _row_to_draft(row: dict) -> Draft:
    """Convert a database row dict to a Draft dataclass.

    Args:
        row: A dict from ``pg_pool.fetch_all()`` (RealDictCursor).

    Returns:
        The corresponding Draft object.
    """
    # psycopg2 returns lists for TEXT[] columns
    tags = list(row.get("tags") or [])

    return Draft(
        id=row["id"],
        name=row["name"],
        draft_type=row["draft_type"],
        path=row["path"],
        author=row["author"],
        status=row["status"],
        visibility=row["visibility"],
        favorite=row["favorite"],
        description=row["description"],
        tags=tags,
        created_at=_fmt_timestamp(row.get("created_at")),
        updated_at=_fmt_timestamp(row.get("updated_at")),
        thumbnail_path=row.get("thumbnail_path", ""),
        use_count=row.get("use_count", 0),
    )


def _fmt_timestamp(ts) -> str:
    """Safely format a PG timestamp to 'YYYY-MM-DD' string."""
    if ts is None:
        return ""
    try:
        return ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)[:10]
    except Exception:
        return str(ts)[:10]


# ── Storage implementation ──────────────────────────────────────────────


class PGDraftStorage(DraftStorage):
    """Draft storage backed by PostgreSQL.

    Requires ``browser.drafts`` table — run
    ``ensure_schema()`` from :mod:`~asset_browser.db.schema` first.
    """

    def list_drafts(self) -> list[Draft]:
        """Return all drafts ordered by id."""
        if not pg_pool.available:
            logger.warning("PG unavailable, cannot list drafts")
            return []
        rows = pg_pool.fetch_all(_SELECT_ALL)
        return [_row_to_draft(r) for r in rows]

    def get_draft(self, draft_id: int) -> Optional[Draft]:
        """Retrieve a single draft by id."""
        row = pg_pool.fetch_one(_SELECT_BY_ID, (draft_id,))
        return _row_to_draft(row) if row else None

    def add_draft(self, draft: Draft) -> Draft:
        """Insert a new draft and return it with the assigned id."""
        params = _draft_to_params(draft)
        row = pg_pool.fetch_one(_INSERT, params)
        if row:
            draft.id = row["id"]
            logger.debug("PG added draft %d: %s", draft.id, draft.name)
        else:
            logger.warning("PG add_draft returned no id for %s", draft.name)
        return draft

    def update_draft(self, draft: Draft) -> Draft:
        """Update an existing draft.

        Raises:
            KeyError: If no draft with ``draft.id`` exists.
        """
        params = _draft_to_params(draft)
        rc = pg_pool.execute(_UPDATE, params)
        if rc < 0:
            raise KeyError(f"PG update failed for draft {draft.id}")
        if rc == 0:
            raise KeyError(f"Draft with id {draft.id} not found")
        logger.debug("PG updated draft %d: %s", draft.id, draft.name)
        return draft

    def delete_draft(self, draft_id: int) -> bool:
        """Remove a draft by id.

        Returns:
            ``True`` if found and deleted, ``False`` otherwise.
        """
        rc = pg_pool.execute(_DELETE, (draft_id,))
        if rc < 0:
            # Error during deletion — could be connection issue
            logger.error("PG delete_draft failed for id %d", draft_id)
            return False
        deleted = rc > 0
        if deleted:
            logger.debug("PG deleted draft %d", draft_id)
        else:
            logger.debug("PG delete_draft: draft %d not found", draft_id)
        return deleted
