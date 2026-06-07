"""Tests for JSONDraftStorage — file-based draft persistence."""

from __future__ import annotations

import os
import tempfile

import pytest

from asset_browser.core.models import Draft
from asset_browser.db.json_store import JSONDraftStorage


@pytest.fixture
def tmp_json_path() -> str:
    """Yield a temporary JSON file path, cleaned up after the test."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.isfile(path):
        os.unlink(path)


@pytest.fixture
def store(tmp_json_path: str) -> JSONDraftStorage:
    """Return a JSONDraftStorage backed by a temporary file."""
    return JSONDraftStorage(tmp_json_path)


@pytest.fixture
def sample_draft() -> Draft:
    return Draft(id=0, name="test_gizmo", draft_type="template", path="/tmp/test.nk")


# ── Initial state ───────────────────────────────────────────────────────


class TestInit:
    def test_empty_store(self, store: JSONDraftStorage):
        assert store.list_drafts() == []

    def test_loads_existing_data(self, tmp_json_path: str):
        """Data written by one store instance is readable by another."""
        s1 = JSONDraftStorage(tmp_json_path)
        s1.add_draft(Draft(id=0, name="persist_me", draft_type="image", path="/a.png"))

        s2 = JSONDraftStorage(tmp_json_path)
        assert len(s2.list_drafts()) == 1
        assert s2.list_drafts()[0].name == "persist_me"

    def test_corrupted_file_returns_empty(self, tmp_json_path: str):
        """A malformed JSON file should not crash the store."""
        with open(tmp_json_path, "w") as f:
            f.write("not valid json {{{")
        store = JSONDraftStorage(tmp_json_path)
        assert store.list_drafts() == []


# ── CRUD ────────────────────────────────────────────────────────────────


class TestCRUD:
    def test_add_draft(self, store: JSONDraftStorage, sample_draft: Draft):
        saved = store.add_draft(sample_draft)
        assert saved.id == 1  # first draft gets id 1
        assert saved.name == "test_gizmo"

    def test_add_multiple_drafts(self, store: JSONDraftStorage):
        d1 = store.add_draft(Draft(id=0, name="a", draft_type="template", path=""))
        d2 = store.add_draft(Draft(id=0, name="b", draft_type="image", path=""))
        d3 = store.add_draft(Draft(id=0, name="c", draft_type="video", path=""))
        assert d1.id == 1
        assert d2.id == 2
        assert d3.id == 3

    def test_list_drafts(self, store: JSONDraftStorage):
        store.add_draft(Draft(id=0, name="a", draft_type="template", path=""))
        store.add_draft(Draft(id=0, name="b", draft_type="image", path=""))
        all_drafts = store.list_drafts()
        assert len(all_drafts) == 2

    def test_get_draft_found(self, store: JSONDraftStorage, sample_draft: Draft):
        saved = store.add_draft(sample_draft)
        fetched = store.get_draft(saved.id)
        assert fetched is not None
        assert fetched.name == "test_gizmo"

    def test_get_draft_not_found(self, store: JSONDraftStorage):
        assert store.get_draft(999) is None

    def test_update_draft(self, store: JSONDraftStorage, sample_draft: Draft):
        saved = store.add_draft(sample_draft)
        saved.name = "renamed"
        store.update_draft(saved)
        assert store.get_draft(saved.id).name == "renamed"

    def test_update_draft_not_found(self, store: JSONDraftStorage):
        ghost = Draft(id=999, name="ghost", draft_type="template", path="")
        with pytest.raises(KeyError):
            store.update_draft(ghost)

    def test_delete_draft(self, store: JSONDraftStorage, sample_draft: Draft):
        saved = store.add_draft(sample_draft)
        assert store.delete_draft(saved.id) is True
        assert store.get_draft(saved.id) is None

    def test_delete_draft_not_found(self, store: JSONDraftStorage):
        assert store.delete_draft(999) is False

    def test_favorite_field(self, store: JSONDraftStorage):
        d = store.add_draft(Draft(id=0, name="fav_test", draft_type="template", path="", favorite=True))
        assert d.favorite is True
        fetched = store.get_draft(d.id)
        assert fetched.favorite is True


# ── Edge cases ──────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_tags_preserved(self, store: JSONDraftStorage):
        tags = ["grain", "film", "noise"]
        d = store.add_draft(Draft(id=0, name="tagged", draft_type="template", path="", tags=tags))
        fetched = store.get_draft(d.id)
        assert fetched.tags == tags

    def test_special_characters_in_name(self, store: JSONDraftStorage):
        name = "hello_world_测试_123"
        d = store.add_draft(Draft(id=0, name=name, draft_type="template", path=""))
        assert store.get_draft(d.id).name == name

    def test_add_with_explicit_id_is_overwritten(self, store: JSONDraftStorage):
        """The store should assign its own id."""
        d = Draft(id=999, name="explicit_id", draft_type="template", path="")
        saved = store.add_draft(d)
        assert saved.id != 999  # store assigns new id
