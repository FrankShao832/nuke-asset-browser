#!/Applications/Nuke16.0v3/Nuke16.0v3.app/Contents/Frameworks/Python.framework/Versions/3.11/bin/python3.11
"""Nuke Asset Browser — Save Draft dialog"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QWidget,
)
from PySide6.QtCore import Qt, Signal

from asset_browser.core.models import Draft
from asset_browser.ui.theme import Color, FontSize, Styles


class SaveDraftDialog(QDialog):
    """Dialog for saving a new draft from Node Graph selection"""

    saved = Signal(Draft)  # emitted when user confirms

    def __init__(self, defaults: dict | None = None, parent=None):
        super().__init__(parent)
        self._defaults = defaults or {}
        self._path_override: str | None = None
        self._default_frame_range: str = ""
        self._default_sequence_pattern: str = ""
        self._init_ui()
        self._apply_defaults()

    def _init_ui(self):
        self.setWindowTitle("Save Draft")
        self.setFixedSize(480, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Color.WINDOW};
                border: 1px solid {Color.BORDER};
                border-radius: 8px;
            }}
            QLabel {{
                font-size: {FontSize.TAB};
                color: {Color.TEXT_SECONDARY};
            }}
            QLineEdit, QTextEdit {{
                background-color: {Color.TRANSPARENT};
                border: 1px solid {Color.BORDER};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: {FontSize.TAB};
                color: {Color.TEXT_PRIMARY};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {Color.ACCENT};
            }}
            QComboBox {{
                background-color: {Color.PANEL};
                border: 1px solid {Color.BTN_HOVER};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: {FontSize.TAB};
                color: {Color.TEXT_PRIMARY};
            }}
            QComboBox:focus {{
                border: 1px solid {Color.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Color.WINDOW};
                border: 1px solid {Color.BORDER};
                selection-background-color: {Color.ACCENT};
                color: {Color.TEXT_PRIMARY};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        # root.setSpacing(12)

        # Title
        title = QLabel("📦 Save New Draft")
        title.setStyleSheet(Styles.label_title())
        root.addWidget(title)

        root.addSpacing(4)

        # ── Name ──
        root.addWidget(QLabel("Name *"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g. film_grain_002")
        root.addWidget(self._name_input)

        # ── Type ──
        root.addWidget(QLabel("Type"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(["template", "image", "video", "script", "sequence", "other"])
        root.addWidget(self._type_combo)

        # ── Description ──
        root.addWidget(QLabel("Description (optional)"))
        self._desc_input = QTextEdit()
        self._desc_input.setPlaceholderText("Brief description of this draft...")
        self._desc_input.setFixedHeight(60)
        self._desc_input.setObjectName("descInput")
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
        cancel_btn.setStyleSheet(Styles.secondary_button())
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.setFixedSize(100, 34)
        save_btn.setStyleSheet(Styles.primary_button())
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
        if "path" in self._defaults:
            self._path_override = self._defaults["path"]
        if "tags" in self._defaults:
            tags = self._defaults["tags"]
            if isinstance(tags, list):
                self._tags_input.setText(", ".join(tags))
        if "description" in self._defaults:
            self._desc_input.setPlainText(self._defaults["description"])
        # Sequence fields passed through for Draft creation
        self._default_frame_range = self._defaults.get("frame_range", "")
        self._default_sequence_pattern = self._defaults.get("sequence_pattern", "")

    def _on_save(self):
        name = self._name_input.text().strip()
        if not name:
            self._name_input.setStyleSheet("""
                background-color: transparent;
                border: 1px solid #e53935;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 15px;
                color: #ddd;
            """)
            self._name_input.setFocus()
            return

        # Generate an ID (negative for new drafts, storage will assign real ID)
        import time
        # Use exported file path if provided, otherwise default
        if self._path_override:
            draft_path = self._path_override
        else:
            draft_path = f"/tools/{name}.nk"

        draft = Draft(
            id=int(time.time() * 1000) % 100000,  # temp ID
            name=name,
            draft_type=self._type_combo.currentText(),
            path=draft_path,
            author="frank",
            status="draft",
            visibility=self._vis_combo.currentText(),
            description=self._desc_input.toPlainText().strip(),
            tags=[t.strip() for t in self._tags_input.text().split(",") if t.strip()],
            frame_range=self._default_frame_range,
            sequence_pattern=self._default_sequence_pattern,
        )
        self.saved.emit(draft)
        self.accept()


# ═════════════════════════════════════════════════════════════════════
#  Standalone entry point (for UI debugging without Nuke)
# ═════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    import os

    # Add project root's parent to path so `import asset_browser` works
    _root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    if _root not in sys.path:
        sys.path.insert(0, _root)

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Mock a Draft instance so the dialog can emit
    dialog = SaveDraftDialog(defaults={
        "name": "my_grade_node",
        "draft_type": "Gizmo",
        "description": "A quick grade for temp matching",
        "tags": "grade,color,lookdev",
        "visibility": "Public",
        "path": "/tools/my_grade_node.nk",
    })

    def _on_saved(draft):
        print(f"✅ Draft saved: {draft}")
        print(f"   name  : {draft.name}")
        print(f"   type  : {draft.draft_type}")
        print(f"   path  : {draft.path}")
        print(f"   vis   : {draft.visibility}")
        print(f"   desc  : {draft.description}")
        print(f"   tags  : {draft.tags}")

    dialog.saved.connect(_on_saved)
    dialog.show()

    sys.exit(app.exec())
