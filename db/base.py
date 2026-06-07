"""Nuke Asset Browser — Storage abstraction layer.

Every storage backend (JSON, PostgreSQL, …) implements the
:class:`DraftStorage` interface so that UI code never depends on a
particular storage technology.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from asset_browser.core.models import Draft


class DraftStorage(ABC):
    """Abstract interface for draft persistence.

    All CRUD operations are defined here.  Callers interact exclusively
    through these methods — swapping the backing store should never
    require UI changes.
    """

    @abstractmethod
    def list_drafts(self) -> list[Draft]:
        """Return every draft in the store.

        Returns:
            A list of all Draft objects (may be empty).
        """
        ...

    @abstractmethod
    def get_draft(self, draft_id: int) -> Optional[Draft]:
        """Retrieve a single draft by its unique identifier.

        Args:
            draft_id: The numeric id of the draft.

        Returns:
            The matching Draft, or ``None`` if not found.
        """
        ...

    @abstractmethod
    def add_draft(self, draft: Draft) -> Draft:
        """Persist a new draft and return it with an auto-generated id.

        Args:
            draft: The draft to persist (its ``id`` may be ignored/written
                   during storage).

        Returns:
            The persisted Draft with its final ``id`` assigned.
        """
        ...

    @abstractmethod
    def update_draft(self, draft: Draft) -> Draft:
        """Replace an existing draft in the store.

        Args:
            draft: The draft to update.  Must have an ``id`` that exists
                   in the store.

        Returns:
            The updated Draft.

        Raises:
            KeyError: If no draft with ``draft.id`` exists.
        """
        ...

    @abstractmethod
    def delete_draft(self, draft_id: int) -> bool:
        """Remove a draft by its id.

        Args:
            draft_id: The id of the draft to remove.

        Returns:
            ``True`` if the draft was found and deleted, ``False`` if
            no draft with that id existed.
        """
        ...
