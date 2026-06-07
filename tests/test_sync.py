"""Tests for storage auto-select & sync engine."""

from __future__ import annotations

import os
import tempfile

import pytest

from asset_browser.db.sync import get_storage, force_storage, sync_to_pg
from asset_browser.db.json_store import JSONDraftStorage
from asset_browser.db.pg_store import PGDraftStorage
from asset_browser.db.connection import pg_pool


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_state():
    """Reset the global storage cache before each test."""
    force_storage(None)
    yield
    force_storage(None)


# ── Auto-select ─────────────────────────────────────────────────────────


class TestAutoSelect:
    def test_auto_detect_prefers_pg(self):
        """When PG is running, get_storage() should return PGDraftStorage."""
        store = get_storage()
        if pg_pool.ensure_connected():
            assert isinstance(store, PGDraftStorage)
        else:
            assert isinstance(store, JSONDraftStorage)

    def test_force_json(self):
        force_storage("json")
        store = get_storage()
        assert isinstance(store, JSONDraftStorage)

    def test_force_pg(self):
        if not pg_pool.ensure_connected():
            pytest.skip("PG unavailable")
        force_storage("pg")
        store = get_storage()
        assert isinstance(store, PGDraftStorage)

    def test_force_none_resets_to_auto(self):
        force_storage("json")
        force_storage(None)
        store = get_storage()
        if pg_pool.ensure_connected():
            assert isinstance(store, PGDraftStorage)

    def test_same_instance_cached(self):
        """get_storage() should return the same instance on repeated calls."""
        s1 = get_storage()
        s2 = get_storage()
        assert s1 is s2


# ── Sync ────────────────────────────────────────────────────────────────


@pytest.mark.skipif(
    not pg_pool.ensure_connected(),
    reason="PostgreSQL is not running",
)
class TestSync:
    @pytest.fixture(autouse=True)
    def clean_pg(self):
        pg_pool.execute("DELETE FROM browser.drafts")
        yield

    def test_sync_empty_json(self):
        """Syncing when JSON is empty should not error."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        orig = JSONDraftStorage._DEFAULT_JSON_PATH
        JSONDraftStorage._DEFAULT_JSON_PATH = path
        try:
            n = sync_to_pg()
            assert n == 0
        finally:
            JSONDraftStorage._DEFAULT_JSON_PATH = orig
            if os.path.isfile(path):
                os.unlink(path)

    def test_sync_adds_drafts_to_pg(self):
        """Drafts from JSON should appear in PG after sync."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        # Seed JSON with a draft
        js = JSONDraftStorage(path)
        from asset_browser.core.models import Draft
        js.add_draft(Draft(id=0, name="sync_me", draft_type="template", path="/tmp/s.nk"))

        orig = JSONDraftStorage._DEFAULT_JSON_PATH
        JSONDraftStorage._DEFAULT_JSON_PATH = path
        try:
            n = sync_to_pg()
            assert n == 1

            # Verify in PG
            rows = pg_pool.fetch_all(
                "SELECT name FROM browser.drafts WHERE name = %s", ("sync_me",)
            )
            assert len(rows) == 1
        finally:
            JSONDraftStorage._DEFAULT_JSON_PATH = orig
            if os.path.isfile(path):
                os.unlink(path)
