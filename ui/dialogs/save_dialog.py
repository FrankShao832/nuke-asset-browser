"""Nuke Asset Browser — Save Draft dialog"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QFrame, QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont

from asset_browser.core.models import Draft
from asset_browser.core.thumbnail import get_placeholder_thumbnail


class SaveDraftDialog(QDialog):
    """Dialog for saving a new draft from Node Graph selection"""

    saved = Signal(Draft)  # emitted when user confirms

    def __init__(self, defaults: dict | None = None, parent=None):
        super().__init__(parent)
        self._defaults = defaults or {}
        self._init_ui()
        self._apply_defaults()

    def _init_ui(self):
        self.setWindowTitle("Save Draft")
        self.setFixedSize(480, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #242424;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
            QLabel {
                font-size: 11px;
                color: #bbb;
            }
            QLineEdit, QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
                color: #ddd;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #3a7bd5;
            }
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
                color: #ddd;
            }
            QComboBox:focus {
                border: 1px solid #3a7bd5;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                border: 1px solid #3a3a3a;
                selection-background-color: #3a7bd5;
                color: #ddd;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        # Title
        title = QLabel("📦 Save New Draft")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #fff;")
        root.addWidget(title)

        root.addSpacing(4)

        # ── Preview thumbnail ──
        thumb_row = QHBoxLayout()
        self._thumb_label = QLabel()
        self._thumb_label.setFixedSize(120, 68)
        self._thumb_label.setAlignment(Qt.AlignCenter)
        thumb_row.addWidget(self._thumb_label)
        thumb_row.addStretch()
        root.addLayout(thumb_row)

        # ── Name ──
        root.addWidget(QLabel("Name *"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g. film_grain_002")
        root.addWidget(self._name_input)

        # ── Type ──
        root.addWidget(QLabel("Type"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(["template", "image", "video", "script", "other"])
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        root.addWidget(self._type_combo)

        # ── Description ──
        root.addWidget(QLabel("Description (optional)"))
        self._desc_input = QTextEdit()
        self._desc_input.setPlaceholderText("Brief description of this draft...")
        self._desc_input.setFixedHeight(60)
        root.addWidget(self._desc_input)

        # ── Tags ──
        root.addWidget(QLabel("Tags (comma separated)"))
        self._tags_input = QLineEdit()
        self._tags_input.setPlaceholderText("e.g. grain, film, noise")
        root.addWidget(self._tags_input)

        # ── Visibility ──
        vis_row = QHBoxLayout()
        vis_row.addWidget(QLabel("Visibility"))
        self._vis_combo = QComboBox()
        self._vis_combo.addItems(["private", "shared"])
        vis_row.addWidget(self._vis_combo, stretch=1)
        root.addLayout(vis_row)

        root.addStretch()

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 34)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 6px;
                font-size: 12px;
                color: #bbb;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                color: #ddd;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.setFixedSize(100, 34)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a7bd5;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #4a8be5;
            }
            QPushButton:pressed {
                background-color: #2a6bc5;
            }
        """)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        root.addLayout(btn_row)

    def _apply_defaults(self):
        if "name" in self._defaults:
            self._name_input.setText(self._defaults["name"])
        if "draft_type" in self._defaults:
            idx = self._type_combo.findText(self._defaults["draft_type"])
            if idx >= 0:
                self._type_combo.setCurrentIndex(idx)
        # Update thumbnail preview
        self._on_type_changed(self._type_combo.currentText())

    def _on_type_changed(self, draft_type: str):
        pix = get_placeholder_thumbnail(draft_type, (120, 68))
        self._thumb_label.setPixmap(pix)

    def _on_save(self):
        name = self._name_input.text().strip()
        if not name:
            self._name_input.setStyleSheet("""
                background-color: #1e1e1e;
                border: 1px solid #e53935;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
                color: #ddd;
            """)
            self._name_input.setFocus()
            return

        # Generate an ID (negative for new drafts, storage will assign real ID)
        import time
        draft = Draft(
            id=int(time.time() * 1000) % 100000,  # temp ID
            name=name,
            draft_type=self._type_combo.currentText(),
            path=f"/tools/{name}.nk",
            author="frank",
            status="draft",
            visibility=self._vis_combo.currentText(),
            description=self._desc_input.toPlainText().strip(),
            tags=[t.strip() for t in self._tags_input.text().split(",") if t.strip()],
        )
        self.saved.emit(draft)
        self.accept()
