"""Tests for PGDraftStorage — PostgreSQL-backed draft persistence.

These tests require a running PostgreSQL instance with the ``pipeline_db``
database and ``browser.drafts`` schema.  They are skipped automatically if
PG is unreachable.
"""

from __future__ import annotations

import pytest

from asset_browser.core.models import Draft
from asset_browser.db.connection import pg_pool
from asset_browser.db.pg_store import PGDraftStorage
from asset_browser.db.schema import ensure_schema

# ── Skip if PG unavailable ──────────────────────────────────────────────

pg_available = pg_pool.ensure_connected()
if pg_available:
    ensure_schema()


pytestmark = pytest.mark.skipif(
    not pg_available,
    reason="PostgreSQL is not running or pipeline_db is unreachable",
)


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clean_table():
    """Ensure a clean browser.drafts table before each test."""
    pg_pool.execute("DELETE FROM browser.drafts")
    yield


@pytest.fixture
def store() -> PGDraftStorage:
    return PGDraftStorage()


@pytest.fixture
def sample_draft() -> Draft:
    return Draft(id=0, name="test_gizmo", draft_type="template", path="/tmp/test.nk")


# ── CRUD ────────────────────────────────────────────────────────────────


class TestCRUD:
    def test_add_draft(self, store: PGDraftStorage, sample_draft: Draft):
        saved = store.add_draft(sample_draft)
        assert saved.id > 0
        assert saved.name == "test_gizmo"

    def test_add_multiple_drafts(self, store: PGDraftStorage):
        d1 = store.add_draft(Draft(id=0, name="a", draft_type="template", path=""))
        d2 = store.add_draft(Draft(id=0, name="b", draft_type="image", path=""))
        assert d2.id > d1.id  # SERIAL assigns increasing ids

    def test_list_drafts(self, store: PGDraftStorage):
        store.add_draft(Draft(id=0, name="a", draft_type="template", path=""))
        store.add_draft(Draft(id=0, name="b", draft_type="image", path=""))
        all_drafts = store.list_drafts()
        assert len(all_drafts) == 2

    def test_get_draft_found(self, store: PGDraftStorage, sample_draft: Draft):
        saved = store.add_draft(sample_draft)
        fetched = store.get_draft(saved.id)
        assert fetched is not None
        assert fetched.name == "test_gizmo"

    def test_get_draft_not_found(self, store: PGDraftStorage):
        assert store.get_draft(99999) is None

    def test_update_draft(self, store: PGDraftStorage, sample_draft: Draft):
        saved = store.add_draft(sample_draft)
        saved.name = "renamed"
        store.update_draft(saved)
        assert store.get_draft(saved.id).name == "renamed"

    def test_update_draft_not_found(self, store: PGDraftStorage):
        ghost = Draft(id=99999, name="ghost", draft_type="template", path="")
        with pytest.raises(KeyError):
            store.update_draft(ghost)

    def test_delete_draft(self, store: PGDraftStorage, sample_draft: Draft):
        saved = store.add_draft(sample_draft)
        assert store.delete_draft(saved.id) is True
        assert store.get_draft(saved.id) is None

    def test_delete_draft_not_found(self, store: PGDraftStorage):
        assert store.delete_draft(99999) is False

    def test_favorite_field(self, store: PGDraftStorage):
        d = store.add_draft(Draft(id=0, name="fav_test", draft_type="template", path="", favorite=True))
        assert d.favorite is True
        fetched = store.get_draft(d.id)
        assert fetched.favorite is True


# ── Edge cases ──────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_tags_preserved(self, store: PGDraftStorage):
        tags = ["grain", "film", "noise"]
        d = store.add_draft(Draft(id=0, name="tagged", draft_type="template", path="", tags=tags))
        fetched = store.get_draft(d.id)
        assert fetched.tags == tags

    def test_special_characters(self, store: PGDraftStorage):
        name = "hello_world_测试_123"
        d = store.add_draft(Draft(id=0, name=name, draft_type="template", path=""))
        assert store.get_draft(d.id).name == name

    def test_large_text_fields(self, store: PGDraftStorage):
        long_desc = "A" * 10000
        d = store.add_draft(Draft(id=0, name="long", draft_type="template", path="", description=long_desc))
        fetched = store.get_draft(d.id)
        assert fetched.description == long_desc

    def test_use_count_preserved(self, store: PGDraftStorage):
        d = store.add_draft(Draft(id=0, name="popular", draft_type="template", path="", use_count=42))
        fetched = store.get_draft(d.id)
        assert fetched.use_count == 42
