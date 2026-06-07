"""Nuke Asset Browser — Search & Filter Engine (Phase 1: in-memory)"""

from __future__ import annotations

from typing import Callable

from asset_browser.core.models import Draft


class DraftSearch:
    """In-memory search and filter engine for Draft objects"""

    def __init__(self):
        self._drafts: list[Draft] = []
        self._keyword = ""
        self._filter = "all"       # all / mine / shared / favorites / published
        self._sort = "latest"      # latest / hottest
        self._current_user = "frank"

    # ── Input API ──

    def set_drafts(self, drafts: list[Draft]):
        """Set the full draft pool"""
        self._drafts = drafts

    def set_keyword(self, keyword: str):
        """Set search keyword"""
        self._keyword = keyword.strip().lower()

    def set_filter(self, filter_id: str):
        """Set category filter: all / mine / shared / favorites / published"""
        self._filter = filter_id

    def set_sort(self, sort_key: str):
        """Set sort order: latest / hottest"""
        self._sort = sort_key

    def set_current_user(self, user: str):
        """Set current user name for 'mine' filter"""
        self._current_user = user

    # ── Computed results ──

    def search(self, keyword: str | None = None) -> list[Draft]:
        """Run search + filter + sort, return filtered drafts"""
        if keyword is not None:
            self._keyword = keyword.strip().lower()

        results = self._drafts

        # Apply keyword search
        if self._keyword:
            kw = self._keyword
            results = [
                d for d in results
                if kw in d.name.lower()
                or kw in d.description.lower()
                or any(kw in t.lower() for t in d.tags)
                or kw in d.draft_type.lower()
            ]

        # Apply category filter
        results = self._apply_filter(results)

        # Apply sort
        results = self._apply_sort(results)

        return results

    def search_with_filters(
        self,
        keyword: str | None = None,
        filter_id: str | None = None,
        sort_key: str | None = None,
    ) -> list[Draft]:
        """Convenience: run all at once"""
        if keyword is not None:
            self._keyword = keyword.strip().lower()
        if filter_id is not None:
            self._filter = filter_id
        if sort_key is not None:
            self._sort = sort_key
        return self.search()

    def get_counts(self) -> dict[str, int]:
        """Compute badge counts for each filter category"""
        all_drafts = self._drafts
        return {
            "all": len(all_drafts),
            "mine": len([d for d in all_drafts if d.author == self._current_user]),
            "shared": len([d for d in all_drafts if d.visibility == "shared"]),
            "favorites": len([d for d in all_drafts if d.favorite]),
            "published": len([d for d in all_drafts if d.status == "published"]),
        }

    def get_draft(self, draft_id: int) -> Draft | None:
        """Lookup a single draft by ID"""
        for d in self._drafts:
            if d.id == draft_id:
                return d
        return None

    # ── Internal ──

    def _apply_filter(self, drafts: list[Draft]) -> list[Draft]:
        match self._filter:
            case "all":
                return drafts
            case "mine":
                return [d for d in drafts if d.author == self._current_user]
            case "shared":
                return [d for d in drafts if d.visibility == "shared"]
            case "favorites":
                return [d for d in drafts if d.favorite]
            case "published":
                return [d for d in drafts if d.status == "published"]
            case _:
                return drafts

    def _apply_sort(self, drafts: list[Draft]) -> list[Draft]:
        match self._sort:
            case "latest":
                return sorted(drafts, key=lambda d: d.id, reverse=True)
            case "hottest":
                return sorted(drafts, key=lambda d: d.use_count, reverse=True)
            case _:
                return drafts
