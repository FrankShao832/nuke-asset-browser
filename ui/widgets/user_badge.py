"""Nuke Asset Browser — User status badge (naked)"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class UserBadge(QWidget):
    """Displays current user name and role"""

    def __init__(self, name: str = "Frank", role: str = "Admin", parent=None):
        super().__init__(parent)
        self._name = name
        self._role = role

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        user_prefix = QLabel("User:")
        layout.addWidget(user_prefix)

        self._name_label = QLabel(name)
        layout.addWidget(self._name_label)

        role_label = QLabel(f"[{role}]")
        layout.addWidget(role_label)

        layout.addStretch()

    def set_user(self, name: str, role: str = "User"):
        self._name = name
        self._role = role
        self._name_label.setText(name)
