"""Nuke Asset Browser — JSON file-based draft storage.

Lightweight, portable, no external dependencies.  Suitable for
personal use and offline fallback when PostgreSQL is unavailable.

Usage::

    from asset_browser.db.json_store import JSONDraftStorage

    store = JSONDraftStorage()
    drafts = store.list_drafts()
    store.add_draft(my_draft)
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Optional

from asset_browser.core.models import Draft
from asset_browser.db.base import DraftStorage
from asset_browser.utils.logger import get_logger

logger = get_logger(__name__)


class JSONDraftStorage(DraftStorage):
    """Draft storage backed by a single JSON file on disk.

    Keeps an in-memory copy of all drafts for fast reads; writes go
    straight to the JSON file so data survives a restart.
    """

    #: Default location under the Nuke user directory.
    _DEFAULT_JSON_PATH = os.path.join(
        os.path.expanduser("~"), ".nuke", "AssetBrowser", "drafts.json"
    )

    def __init__(self, json_path: Optional[str] = None) -> None:
        """Initialise storage and load any existing drafts from file.

        Args:
            json_path: Path to the JSON file.  If ``None``, defaults to
                       ``~/.nuke/AssetBrowser/drafts.json``.
        """
        self._json_path = json_path or self._DEFAULT_JSON_PATH
        self._drafts: list[Draft] = []
        self._load()
        logger.info(
            "JSON storage ready — %s (%d drafts)",
            self._json_path,
            len(self._drafts),
        )

    # ── CRUD ────────────────────────────────────────────────────────────

    def list_drafts(self) -> list[Draft]:
        """Return all drafts from the in-memory cache.

        Returns:
            A list of all Draft objects (never ``None``).
        """
        return list(self._drafts)

    def get_draft(self, draft_id: int) -> Optional[Draft]:
        """Retrieve a draft by its id.

        Args:
            draft_id: Numeric draft identifier.

        Returns:
            The matching Draft, or ``None`` if not found.
        """
        for d in self._drafts:
            if d.id == draft_id:
                return d
        return None

    def add_draft(self, draft: Draft) -> Draft:
        """Persist a new draft with an auto-generated id.

        Args:
            draft: The draft to add (its ``id`` field is overwritten).

        Returns:
            The persisted Draft with its assigned id.
        """
        draft.id = self._next_id()
        self._drafts.append(draft)
        self._save()
        logger.debug("Added draft %d: %s", draft.id, draft.name)
        return draft

    def update_draft(self, draft: Draft) -> Draft:
        """Replace an existing draft in-place.

        Args:
            draft: Draft with an ``id`` that already exists in the store.

        Returns:
            The updated Draft.

        Raises:
            KeyError: If no draft with ``draft.id`` exists.
        """
        for i, existing in enumerate(self._drafts):
            if existing.id == draft.id:
                self._drafts[i] = draft
                self._save()
                logger.debug("Updated draft %d: %s", draft.id, draft.name)
                return draft
        raise KeyError(f"Draft with id {draft.id} not found")

    def delete_draft(self, draft_id: int) -> bool:
        """Remove a draft by its id.

        Args:
            draft_id: The id of the draft to remove.

        Returns:
            ``True`` if found and deleted, ``False`` if not found.
        """
        for i, d in enumerate(self._drafts):
            if d.id == draft_id:
                del self._drafts[i]
                self._save()
                logger.debug("Deleted draft %d: %s", draft_id, d.name)
                return True
        logger.warning("Attempted to delete non-existent draft %d", draft_id)
        return False

    # ── Internal helpers ────────────────────────────────────────────────

    def _load(self) -> None:
        """Load drafts from the JSON file into ``_drafts``.

        If the file is missing or malformed, ``_drafts`` stays empty.
        """
        if not os.path.isfile(self._json_path):
            self._drafts = []
            return

        try:
            with open(self._json_path, "r") as f:
                data = json.load(f)
            self._drafts = [Draft(**item) for item in data]
        except Exception as exc:
            logger.warning("Failed to load drafts from %s: %s", self._json_path, exc)
            self._drafts = []

    def _save(self) -> None:
        """Persist every draft to the JSON file."""
        try:
            os.makedirs(os.path.dirname(self._json_path), exist_ok=True)
            with open(self._json_path, "w") as f:
                json.dump(
                    [asdict(d) for d in self._drafts],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as exc:
            logger.error("Failed to save drafts to %s: %s", self._json_path, exc)

    def _next_id(self) -> int:
        """Return the next available draft id (max + 1)."""
        if not self._drafts:
            return 1
        return max(d.id for d in self._drafts) + 1
