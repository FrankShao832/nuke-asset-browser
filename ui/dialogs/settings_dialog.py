"""Nuke Asset Browser — Settings dialog"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QTabWidget,
    QWidget, QMessageBox,
)
from PySide6.QtCore import Qt

from asset_browser.ui.theme import Color, FontSize, Styles


class SettingsDialog(QDialog):
    """Application settings — Database, Cache, Paths, Thumbnails"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Settings")
        self.setFixedSize(520, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Color.WINDOW};
                border: 1px solid {Color.BORDER};
                border-radius: 8px;
            }}
            QLabel {{
                font-size: {FontSize.BODY};
                color: {Color.TEXT_SECONDARY};
            }}
            QLineEdit {{
                background-color: {Color.PANEL};
                border: 1px solid {Color.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: {FontSize.BODY};
                color: {Color.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 1px solid {Color.ACCENT};
            }}
            QPushButton {{
                background-color: {Color.BTN_NORMAL};
                border: 1px solid {Color.BTN_HOVER};
                border-radius: 4px;
                padding: 6px 16px;
                font-size: {FontSize.BUTTON};
                color: {Color.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background-color: {Color.BTN_HOVER};
                color: {Color.TEXT_PRIMARY};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # Title
        title = QLabel("⚙️ Settings")
        title.setStyleSheet(Styles.label_title())
        root.addWidget(title)

        # ── Tabs ──
        tabs = QTabWidget()
        tabs.setStyleSheet(Styles.tab_widget())

        # Tab 1: Database
        db_tab = QWidget()
        db_root = QVBoxLayout(db_tab)
        db_center = QHBoxLayout()
        db_center.addStretch()
        db_layout = QFormLayout()
        db_layout.setSpacing(8)
        db_center.addLayout(db_layout)
        db_center.addStretch()
        db_root.addLayout(db_center)
        db_root.addStretch()

        db_layout.addRow(QLabel("PostgreSQL Connection"))

        self._db_host = QLineEdit("localhost")
        self._db_host.setMaximumWidth(220)
        db_layout.addRow("Host:", self._db_host)

        self._db_port = QLineEdit("5432")
        self._db_port.setMaximumWidth(220)
        self._db_port.setPlaceholderText("1–65535")
        db_layout.addRow("Port:", self._db_port)

        self._db_name = QLineEdit("asset_browser")
        self._db_name.setMaximumWidth(220)
        db_layout.addRow("Database:", self._db_name)

        self._db_user = QLineEdit("frank")
        self._db_user.setMaximumWidth(220)
        db_layout.addRow("User:", self._db_user)

        self._db_pass = QLineEdit()
        self._db_pass.setMaximumWidth(220)
        self._db_pass.setEchoMode(QLineEdit.Password)
        self._db_pass.setPlaceholderText("******")
        db_layout.addRow("Password:", self._db_pass)

        test_btn = QPushButton("🔌 Test Connection")
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.SUCCESS_BG};
                border: 1px solid #3a7a3a;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 11px;
                color: #4caf50;
            }}
            QPushButton:hover {{
                background-color: {Color.SUCCESS_BG_HOVER};
            }}
        """)
        test_btn.clicked.connect(self._test_connection)
        db_layout.addRow("", test_btn)

        tabs.addTab(db_tab, "Database")

        # Tab 2: Cache
        cache_tab = QWidget()
        cache_layout = QFormLayout(cache_tab)
        cache_layout.setSpacing(8)
        cache_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self._cache_path = QLineEdit("~/.asset_browser/cache")
        cache_layout.addRow("Cache Path:", self._cache_path)

        self._ffmpeg_path = QLineEdit("/usr/local/bin/ffmpeg")
        cache_layout.addRow("FFmpeg Path:", self._ffmpeg_path)

        tabs.addTab(cache_tab, "Cache")

        # Tab 3: Thumbnails
        thumb_tab = QWidget()
        thumb_layout = QFormLayout(thumb_tab)
        thumb_layout.setSpacing(8)

        self._thumb_quality = QLineEdit("85")
        self._thumb_quality.setFixedWidth(50)
        self._thumb_quality.setPlaceholderText("10–100")
        thumb_layout.addRow("Quality (%):", self._thumb_quality)

        self._thumb_width = QLineEdit("260")
        self._thumb_width.setFixedWidth(50)
        self._thumb_width.setPlaceholderText("100–1024")
        thumb_layout.addRow("Max Width (px):", self._thumb_width)

        tabs.addTab(thumb_tab, "Thumbnails")

        root.addWidget(tabs, stretch=1)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(Styles.secondary_button())
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet(Styles.primary_button())
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(save_btn)

        root.addLayout(btn_row)

    def _test_connection(self):
        QMessageBox.information(self, "Test Connection",
                                "🔌 Database connection test\n\n"
                                "Feature coming in Phase 2.\n"
                                "Current: Mock Mode (no database required).")
