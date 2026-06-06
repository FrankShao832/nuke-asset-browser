"""Nuke Asset Browser — Search Bar Widget (naked)"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QFrame,
)
from PySide6.QtCore import Signal, Qt, QTimer


class SearchBar(QWidget):
    """Real-time search bar with debounce."""

    search_text_changed = Signal(str)

    def __init__(self, placeholder: str = "Search drafts by name, tag, or path...", parent=None):
        super().__init__(parent)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._emit_search)

        self._init_ui(placeholder)
        self._connect_signals()

    def _init_ui(self, placeholder: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        container = QFrame()
        container.setObjectName("searchBarFrame")
        container.setFixedHeight(32)
        container.setStyleSheet("""
            #searchBarFrame {
                background-color: #1e1e1e;
                border-radius: 6px;
            }
        """)

        frame_layout = QHBoxLayout(container)
        frame_layout.setContentsMargins(8, 0, 8, 0)
        frame_layout.setSpacing(4)

        icon_btn = QPushButton("🔍")
        icon_btn.setFixedSize(24, 24)
        icon_btn.setFlat(True)
        icon_btn.setEnabled(False)
        frame_layout.addWidget(icon_btn)

        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setClearButtonEnabled(True)
        self._input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                font-size: 13px;
                color: #e0e0e0;
                padding: 4px 0;
            }
            QLineEdit::placeholder {
                color: #666;
            }
        """)
        frame_layout.addWidget(self._input, stretch=1)

        layout.addWidget(container)

    def _connect_signals(self):
        self._input.textChanged.connect(self._on_text_changed)
        self._input.returnPressed.connect(self._emit_search)

    def _on_text_changed(self, text: str):
        self._debounce_timer.stop()
        self._debounce_timer.start()

    def _emit_search(self):
        text = self._input.text().strip()
        self.search_text_changed.emit(text)

    def text(self) -> str:
        return self._input.text().strip()

    def clear(self):
        self._input.clear()

    def setFocus(self):
        self._input.setFocus()
        self._input.selectAll()
