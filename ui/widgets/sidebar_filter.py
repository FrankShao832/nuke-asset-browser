"""Nuke Asset Browser — Sidebar Filter Panel"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea,
)
from PySide6.QtCore import Signal, Qt

from asset_browser.ui.theme import Color, FontSize, Styles


class _FilterButton(QWidget):
    """A single filter item: icon + label + count badge"""

    clicked = Signal(str)

    def __init__(self, filter_id: str, icon: str, label: str,
                 count: int = 0, parent=None):
        super().__init__(parent)
        self._filter_id = filter_id
        self._active = False
        self.setObjectName("SidebarFilterButton")
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 0, 11, 0)
        layout.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setFixedWidth(20)
        icon_label.setStyleSheet(f"background: {Color.TRANSPARENT};")
        layout.addWidget(icon_label)

        self._label = QLabel(label)
        self._label.setStyleSheet(
            f"background: {Color.TRANSPARENT}; color: {Color.TEXT_SECONDARY};"
        )
        layout.addWidget(self._label, stretch=1)

        self._badge = QLabel(str(count))
        self._badge.setFixedSize(20, 18)
        self._badge.setStyleSheet(
            f"background: {Color.TRANSPARENT}; color: {Color.TEXT_MUTED};"
        )
        self._badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._badge)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.setStyleSheet("")
            self._label.setStyleSheet(
                f"color: {Color.TEXT_TITLE}; font-weight: 700; "
                f"background: {Color.TRANSPARENT};"
            )
            self._badge.setStyleSheet(
                f"color: {Color.TEXT_TITLE}; font-weight: 700; "
                f"background: {Color.TRANSPARENT};"
            )
        else:
            self.setStyleSheet("")
            self._label.setStyleSheet(
                f"color: {Color.TEXT_SECONDARY}; background: {Color.TRANSPARENT};"
            )
            self._badge.setStyleSheet(
                f"color: {Color.TEXT_MUTED}; background: {Color.TRANSPARENT};"
            )

    def set_count(self, count: int):
        self._badge.setText(str(count))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self._filter_id)


class _SectionLabel(QLabel):
    """Section header label"""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            f"background: {Color.TRANSPARENT}; color: {Color.TEXT_MUTED}; "
            f"font-size: 10px; font-weight: 700; padding: 8px 8px 2px;"
        )


class SidebarFilter(QWidget):
    """Right-side filter panel for draft browsing"""

    filter_changed = Signal(str)
    sort_changed = Signal(str)
    upload_clicked = Signal()
    save_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_buttons: dict[str, _FilterButton] = {}
        self._current_filter = "all"
        self._current_sort = "latest"
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"""
            SidebarFilter {{
                background-color: {Color.PANEL};
                border-radius: 6px;
            }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(Styles.scroll_area())
        scroll.viewport().setStyleSheet(
            f"background: {Color.PANEL}; border-radius: 6px;"
        )
        scroll.verticalScrollBar().setStyleSheet(Styles.scroll_bar())

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(3, 3, 3, 3)
        self._content_layout.setSpacing(2)

        self._content_layout.addWidget(_SectionLabel("TYPE"))
        self._add_filter("all",       "📋", "All")
        self._add_filter("mine",      "👤", "My Drafts")
        self._add_filter("shared",    "👥", "Shared")
        self._add_filter("favorites", "⭐", "Favorites")
        self._add_filter("published", "✅", "Published")

        self._content_layout.addSpacing(12)
        self._content_layout.addWidget(_SectionLabel("SORT BY"))

        sort_row = QHBoxLayout()
        sort_row.setContentsMargins(8, 0, 8, 0)
        sort_row.setSpacing(6)

        self._btn_latest = QPushButton("Latest")
        self._btn_latest.setFixedHeight(28)
        self._btn_latest.setCursor(Qt.PointingHandCursor)
        self._btn_latest.clicked.connect(lambda: self._set_sort("latest"))
        sort_row.addWidget(self._btn_latest)

        self._btn_hottest = QPushButton("Hottest")
        self._btn_hottest.setFixedHeight(28)
        self._btn_hottest.setCursor(Qt.PointingHandCursor)
        self._btn_hottest.clicked.connect(lambda: self._set_sort("hottest"))
        sort_row.addWidget(self._btn_hottest)

        self._content_layout.addLayout(sort_row)
        self._update_sort_style()
        self._content_layout.addStretch()

        upload_frame = QFrame()
        upload_layout = QHBoxLayout(upload_frame)
        upload_layout.setContentsMargins(8, 8, 8, 8)

        self._upload_btn = QPushButton("📤  Upload")
        self._upload_btn.setFixedHeight(36)
        self._upload_btn.setCursor(Qt.PointingHandCursor)
        self._upload_btn.setStyleSheet(Styles.primary_button())
        self._upload_btn.clicked.connect(self.upload_clicked.emit)
        upload_layout.addWidget(self._upload_btn)

        self._content_layout.addWidget(upload_frame)

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        self._set_active_filter("all")

    def _add_filter(self, filter_id: str, icon: str, label: str, count: int = 0):
        btn = _FilterButton(filter_id, icon, label, count)
        btn.clicked.connect(self._on_filter_clicked)
        self._filter_buttons[filter_id] = btn
        self._content_layout.insertWidget(self._content_layout.count() - 2, btn)

    def _on_filter_clicked(self, filter_id: str):
        if filter_id == self._current_filter:
            return
        self._set_active_filter(filter_id)
        self.filter_changed.emit(filter_id)

    def _set_active_filter(self, filter_id: str):
        for fid, btn in self._filter_buttons.items():
            btn.set_active(fid == filter_id)
        self._current_filter = filter_id

    def _set_sort(self, sort_key: str):
        if sort_key == self._current_sort:
            return
        self._current_sort = sort_key
        self._update_sort_style()
        self.sort_changed.emit(sort_key)

    def _update_sort_style(self):
        active = f"""
            QPushButton {{
                background-color: {Color.ACCENT};
                border: none;
                border-radius: 4px;
                font-size: {FontSize.BUTTON};
                font-weight: 600;
                color: {Color.TEXT_TITLE};
            }}
        """
        inactive = f"""
            QPushButton {{
                background-color: {Color.BTN_NORMAL};
                border: none;
                border-radius: 4px;
                font-size: {FontSize.BUTTON};
                color: {Color.TEXT_MUTED};
            }}
            QPushButton:hover {{
                background-color: {Color.BTN_HOVER};
                color: {Color.TEXT_SECONDARY};
            }}
        """
        self._btn_latest.setStyleSheet(
            active if self._current_sort == "latest" else inactive
        )
        self._btn_hottest.setStyleSheet(
            active if self._current_sort == "hottest" else inactive
        )

    def update_counts(self, counts: dict[str, int]):
        for filter_id, count in counts.items():
            if filter_id in self._filter_buttons:
                self._filter_buttons[filter_id].set_count(count)
