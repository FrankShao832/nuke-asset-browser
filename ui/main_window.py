"""Nuke Asset Browser — Main Window (Naked — no stylesheets)"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QProgressBar,
)
from PySide6.QtCore import Qt

from asset_browser.core.models import MOCK_DRAFTS, Draft
from asset_browser.core.search import DraftSearch
from asset_browser.db.json_store import JSONDraftStorage
from asset_browser.db.pg_store import PGDraftStorage
from asset_browser.db.schema import ensure_schema
from asset_browser.utils.logger import get_logger
from asset_browser.ui.theme import Color, FontSize, Styles, master_stylesheet
from asset_browser.ui.widgets.search_bar import SearchBar
from asset_browser.ui.widgets.sidebar_filter import SidebarFilter
from asset_browser.ui.widgets.thumbnail_grid import ThumbnailGrid
from asset_browser.ui.widgets.toast import Toast
from asset_browser.ui.widgets.user_badge import UserBadge
from asset_browser.ui.dialogs.save_dialog import SaveDraftDialog
from asset_browser.ui.dialogs.settings_dialog import SettingsDialog

logger = get_logger(__name__)


class MainWindow(QWidget):
    """Nuke Asset Browser — main window (no custom stylesheets)"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Storage layer ───────────────────────────────────────────────
        self._store = self._init_storage()
        self._drafts = self._store.list_drafts()

        # Seed with mock data on first run (empty store)
        if not self._drafts:
            logger.info("Empty store — seeding with %d mock drafts", len(MOCK_DRAFTS))
            for mock_draft in MOCK_DRAFTS:
                self._store.add_draft(mock_draft)
            self._drafts = self._store.list_drafts()
            logger.info("Seeded %d drafts", len(self._drafts))

        self._search_engine = DraftSearch()
        self._search_engine.set_drafts(self._drafts)

        self._init_ui()
        self._connect_signals()
        self._load_drafts(self._drafts)
        self._refresh()

    # ── Storage initialisation ──────────────────────────────────────────

    def _init_storage(self) -> PGDraftStorage | JSONDraftStorage:
        """Initialise the storage backend.

        Tries PostgreSQL first (ensures schema), falls back to JSON file
        storage if PG is unavailable.

        Returns:
            An initialised store instance.
        """
        global _STORAGE_BACKEND  # noqa: PLW0603

        # Try PostgreSQL
        if ensure_schema():
            try:
                store = PGDraftStorage()
                drafts = store.list_drafts()
                logger.info("PG store ready — %d drafts found", len(drafts))
                _STORAGE_BACKEND = "PostgreSQL"
                return store
            except Exception as exc:
                logger.warning("PG store init failed: %s", exc)
        else:
            logger.info("PG unavailable — falling back to JSON storage")

        # Fallback: JSON file storage
        try:
            store = JSONDraftStorage()
            drafts = store.list_drafts()
            logger.info("JSON store ready — %d drafts found", len(drafts))
            _STORAGE_BACKEND = "JSON"
            return store
        except Exception as exc:
            logger.error("JSON store also failed: %s", exc)
            _STORAGE_BACKEND = "Memory"
            store = JSONDraftStorage()
            logger.warning("Using in-memory fallback store")
            return store

    # ── UI setup ────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("Nuke Asset Browser")
        self.setStyleSheet(master_stylesheet())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 8, 8, 8)
        top_layout.setSpacing(0)

        self._user_badge = UserBadge("Frank", "Admin")
        top_layout.addWidget(self._user_badge)
        top_layout.addStretch()

        self._settings_btn = QPushButton("⚙️")
        self._settings_btn.setFixedSize(32, 32)
        self._settings_btn.setCursor(Qt.PointingHandCursor)
        self._settings_btn.setStyleSheet(Styles.icon_button())
        self._settings_btn.clicked.connect(self._open_settings)
        top_layout.addWidget(self._settings_btn)
        top_layout.addSpacing(7)

        self._search_bar = SearchBar()
        self._search_bar.setFixedWidth(260)
        top_layout.addWidget(self._search_bar, 1, Qt.AlignVCenter)

        root.addWidget(top_bar)

        # ── Body ──
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(8, 0, 8, 0)
        body_layout.setSpacing(6)

        self._grid = ThumbnailGrid()
        body_layout.addWidget(self._grid, stretch=1)

        self._sidebar = SidebarFilter()
        self._sidebar.setFixedWidth(260)
        body_layout.addWidget(self._sidebar)

        root.addWidget(body, stretch=1)

        # ── Status bar ──
        self._status_bar = QWidget()
        status_layout = QHBoxLayout(self._status_bar)
        status_layout.setContentsMargins(8, 6, 8, 6)

        self._status_label = QLabel()
        status_layout.addWidget(self._status_label)

        self._storage_label = QLabel("🟢  PostgreSQL")
        status_layout.addWidget(self._storage_label)

        # ── Import progress bar (hidden by default) ──
        self._import_progress = QProgressBar()
        self._import_progress.setFixedSize(220, 16)
        self._import_progress.setTextVisible(True)
        self._import_progress.setVisible(False)
        self._import_progress.setStyleSheet("""
            QProgressBar {
                background: #3a3a3a;
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                font-size: 11px;
                color: #ccc;
            }
            QProgressBar::chunk {
                background: #3a7bd5;
                border-radius: 2px;
            }
        """)
        status_layout.addWidget(self._import_progress)

        status_layout.addStretch()

        self._count_label = QLabel()
        status_layout.addWidget(self._count_label)

        root.addWidget(self._status_bar)

        # Grid: 6*200 + 5*8(spacing) + 16(margins) = 1256
        # Body: 8+1256+6+260+8 = 1538
        self.setFixedSize(1538, 800)

    def _connect_signals(self):
        self._search_bar.search_text_changed.connect(self._on_search)
        self._sidebar.filter_changed.connect(self._on_filter)
        self._sidebar.sort_changed.connect(self._on_sort)
        self._sidebar.upload_clicked.connect(self._on_upload)
        self._grid.draft_activated.connect(self._on_draft_activated)
        self._grid.delete_requested.connect(self._on_delete_draft)
        self._grid.favorite_toggled.connect(self._on_favorite_toggled)
        self._grid.draft_dropped.connect(self._on_draft_dropped)
        self._grid.drafts_dropped.connect(self._on_drafts_dropped)

    def _load_drafts(self, drafts: list[Draft]):
        self._drafts = drafts
        self._search_engine.set_drafts(drafts)
        self._grid.set_drafts(drafts)
        self._update_counts()
        self._update_status()

    def _refresh(self):
        results = self._search_engine.search()
        self._grid.set_drafts(results)
        self._update_status()

    def _update_status(self):
        current = self._grid._layout.count()
        total = len(self._drafts)
        kw = self._search_engine._keyword
        flt = self._search_engine._filter
        srt = self._search_engine._sort

        backend_icon = "🟢" if _STORAGE_BACKEND == "PostgreSQL" else "🟡" if _STORAGE_BACKEND == "JSON" else "🔴"
        self._storage_label.setText(f"{backend_icon}  {_STORAGE_BACKEND}")

        parts = [f"📂 {flt}"]
        if kw:
            parts.append(f'🔎 "{kw}"')
        parts.append(f"📊 {srt}")
        self._status_label.setText(" · ".join(parts))
        self._count_label.setText(f"Showing {current} of {total} drafts")

    def _update_counts(self):
        counts = self._search_engine.get_counts()
        self._sidebar.update_counts(counts)

    def _on_search(self, keyword: str):
        self._search_engine.set_keyword(keyword)
        self._refresh()

    def _on_filter(self, filter_id: str):
        self._search_engine.set_filter(filter_id)
        self._refresh()

    def _on_sort(self, sort_key: str):
        self._search_engine.set_sort(sort_key)
        self._refresh()

    # ── Public API (called from Nuke right-click) ──────────────────────

    def open_save_dialog_for_nuke(
        self,
        name: str,
        filepath: str,
        draft_type: str = "template",
    ) -> None:
        """Open the save dialog pre-filled with exported Nuke node info.

        Args:
            name: Suggested template name (from node names).
            filepath: Path to the exported .nk file.
            draft_type: Draft type (template/image/video/script).
        """
        import os
        defaults = {
            "name": name,
            "path": filepath,
            "draft_type": draft_type,
        }
        dialog = SaveDraftDialog(defaults, self)

        def _on_saved(draft: Draft) -> None:
            # Rename .nk file to match user-entered draft name
            old_path = filepath
            safe_name = draft.name.strip().replace(" ", "_")
            new_path = os.path.join(os.path.dirname(old_path), f"{safe_name}.nk")
            if old_path != new_path:
                import shutil
                try:
                    shutil.move(old_path, new_path)
                    draft.path = new_path
                except Exception:
                    pass

            draft = self._store.add_draft(draft)
            self._load_drafts(self._store.list_drafts())
            self._refresh()  # apply current sort
            Toast.appear(self, f"📦 Saved: {draft.name}", Toast.SUCCESS)

        dialog.saved.connect(_on_saved)
        dialog.open()

    # ── Internal slots ─────────────────────────────────────────────────

    def _on_upload(self):
        import os
        from asset_browser.core.sequence import detect_sequences, detect_from_file

        def _on_saved(draft: Draft) -> None:
            draft = self._store.add_draft(draft)
            self._load_drafts(self._store.list_drafts())
            self._refresh()
            Toast.appear(self, f"📥 Imported: {draft.name}", Toast.SUCCESS)

        # Step 1: Try folder first, then fall back to individual file
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder containing image sequence"
        )
        if folder:
            seqs = detect_sequences(folder)
            if seqs:
                dialog = SaveDraftDialog({
                    "name": seqs[0].name,
                    "draft_type": "sequence",
                    "path": seqs[0].folder,
                    "description": f"Sequence: {seqs[0].pattern} [{seqs[0].frame_range_str}]",
                    "tags": [seqs[0].ext.lstrip(".")],
                    "frame_range": seqs[0].frame_range_str,
                    "sequence_pattern": seqs[0].pattern,
                }, self)
                dialog.saved.connect(_on_saved)
                dialog.open()
                return

        # Step 2: Pick a single sequence frame file
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select a sequence frame or files", "",
            "Image Files (*.exr *.png *.jpg *.jpeg *.tif *.tiff *.tga *.dpx *.bmp);;All Files (*)"
        )
        if not file_paths:
            return

        for fp in file_paths:
            seq = detect_from_file(fp)
            if seq:
                dialog = SaveDraftDialog({
                    "name": seq.name,
                    "draft_type": "sequence",
                    "path": seq.folder,
                    "description": f"Sequence: {seq.pattern} [{seq.frame_range_str}]",
                    "tags": [seq.ext.lstrip(".")],
                    "frame_range": seq.frame_range_str,
                    "sequence_pattern": seq.pattern,
                }, self)
                dialog.saved.connect(_on_saved)
                dialog.open()
            else:
                # No sequence detected — treat as a single-file draft
                name = os.path.splitext(os.path.basename(fp))[0]
                dialog = SaveDraftDialog({"name": name, "path": fp}, self)
                dialog.saved.connect(_on_saved)
                dialog.open()

    def _on_draft_activated(self, draft_id: int):
        draft = self._search_engine.get_draft(draft_id)
        if draft:
            Toast.appear(self, f"📥 Activated: {draft.name}", Toast.INFO)

    def _on_delete_draft(self, draft_id: int):
        from PySide6.QtWidgets import QMessageBox
        draft = self._store.get_draft(draft_id)
        if not draft:
            return
        reply = QMessageBox.question(
            self, "Delete Draft",
            f'Delete "{draft.name}"?\nThis cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._store.delete_draft(draft_id)
        self._load_drafts(self._store.list_drafts())
        self._refresh()
        Toast.appear(self, f"🗑️ Deleted: {draft.name}", Toast.SUCCESS)

    def _on_draft_dropped(self, draft: Draft):
        """Handle a single draft from drag-drop."""
        added = self._store.add_draft(draft)
        self._load_drafts(self._store.list_drafts())
        self._refresh()
        Toast.appear(self, f"📥 Imported: {draft.name}", Toast.SUCCESS)

    def _on_drafts_dropped(self, drafts: list[Draft]):
        """Handle a batch of drafts from drag-drop (multi-file drop)."""
        total = len(drafts)
        self._import_progress.setRange(0, total)
        self._import_progress.setValue(0)
        self._import_progress.setVisible(True)
        self._import_progress.repaint()

        for i, draft in enumerate(drafts):
            self._store.add_draft(draft)
            self._import_progress.setValue(i + 1)
            self._import_progress.setFormat(f"Importing {i + 1}/{total}…")

        self._load_drafts(self._store.list_drafts())
        self._refresh()
        self._import_progress.setVisible(False)
        Toast.appear(self, f"📥 Imported {total} drafts", Toast.SUCCESS)

    def _on_favorite_toggled(self, draft_id: int, new_state: bool):
        draft = self._store.get_draft(draft_id)
        if draft:
            draft.favorite = new_state
            self._store.update_draft(draft)
            self._update_counts()
            toast_msg = "Favorited" if new_state else "Unfavorited"
            Toast.appear(self, f"{toast_msg}: {draft.name}", Toast.SUCCESS)

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
