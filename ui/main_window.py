"""Nuke Asset Browser — Main Window (Naked — no stylesheets)"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
)
from PySide6.QtCore import Qt

from asset_browser.core.models import MOCK_DRAFTS, Draft
from asset_browser.core.search import DraftSearch
from asset_browser.ui.widgets.search_bar import SearchBar
from asset_browser.ui.widgets.sidebar_filter import SidebarFilter
from asset_browser.ui.widgets.user_badge import UserBadge
from asset_browser.ui.widgets.thumbnail_grid import ThumbnailGrid
from asset_browser.ui.dialogs.save_dialog import SaveDraftDialog
from asset_browser.ui.dialogs.settings_dialog import SettingsDialog


class MainWindow(QWidget):
    """Nuke Asset Browser — main window (no custom stylesheets)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drafts = list(MOCK_DRAFTS)
        self._search_engine = DraftSearch()
        self._search_engine.set_drafts(self._drafts)

        self._init_ui()
        self._connect_signals()
        self._load_drafts(self._drafts)

    def _init_ui(self):
        self.setWindowTitle("Nuke Asset Browser")
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
                color: #d4d4d4;
                background-color: #2b2b2b;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──
        top_bar = QWidget()
        # top_bar.setFixedHeight(48)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 8, 8, 8)
        top_layout.setSpacing(0)

        self._user_badge = UserBadge("Frank", "Admin")
        top_layout.addWidget(self._user_badge)

        top_layout.addStretch()

        self._settings_btn = QPushButton("⚙️")
        self._settings_btn.setFixedSize(32, 32)
        self._settings_btn.setCursor(Qt.PointingHandCursor)
        self._settings_btn.setStyleSheet("""
            QPushButton {
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #333;
                border-radius: 4px;
            }
        """)
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

        self._status_label = QLabel()
        status_layout.addWidget(self._status_label)

        self._storage_label = QLabel("🟢  PostgreSQL")
        status_layout.addWidget(self._storage_label)

        status_layout.addStretch()

        self._count_label = QLabel()
        status_layout.addWidget(self._count_label)

        root.addWidget(self._status_bar)

        # ── Fixed window size for 6 cards per row ──
        # Grid internal: 6*200 + 5*8(spacing) + 16(margins) = 1256
        # Body: 8(left) + 1256(grid) + 6(spacing) + 260(sidebar) + 8(right) = 1538
        self.setFixedSize(1538, 800)

    def _connect_signals(self):
        self._search_bar.search_text_changed.connect(self._on_search)
        self._sidebar.filter_changed.connect(self._on_filter)
        self._sidebar.sort_changed.connect(self._on_sort)
        self._sidebar.upload_clicked.connect(self._on_upload)
        self._grid.draft_activated.connect(self._on_draft_activated)
        self._grid.delete_requested.connect(self._on_delete_draft)
        self._grid.favorite_toggled.connect(self._on_favorite_toggled)

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

        parts = ["🔷 Mock Mode"]
        if kw:
            parts.append(f'🔎 "{kw}"')
        parts.append(f"📂 {flt}")
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

    def _on_upload(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select files to upload as Draft", "", "All Files (*)"
        )
        if not file_paths:
            return
        for fp in file_paths:
            import os
            name = os.path.splitext(os.path.basename(fp))[0]
            dialog = SaveDraftDialog({"name": name}, self)
            if dialog.exec() == SaveDraftDialog.Accepted:
                pass

    def _on_draft_activated(self, draft_id: int):
        draft = self._search_engine.get_draft(draft_id)
        if draft:
            self._status_label.setText(f"📥 Activated: {draft.name}")

    def _on_delete_draft(self, draft_id: int):
        self._drafts = [d for d in self._drafts if d.id != draft_id]
        self._load_drafts(self._drafts)

    def _on_favorite_toggled(self, draft_id: int, new_state: bool):
        self._update_counts()

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
