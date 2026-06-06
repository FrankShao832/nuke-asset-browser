"""Nuke Asset Browser — Draft status badge overlay (naked)"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


STATUS_MAP = {
    "draft":     "📝 Draft",
    "published": "✅ Published",
    "modified":  "✏️ Modified",
}


class DraftBadge(QLabel):
    """Status badge overlay — displayed at top-right of thumbnail"""

    def __init__(self, status: str = "draft", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._status = status
        self.setText(STATUS_MAP.get(status, "📝 Draft"))
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_status(self, status: str):
        self._status = status
        self.setText(STATUS_MAP.get(status, "📝 Draft"))


class FavoriteStar(QLabel):
    """Favorite star overlay — top-left of thumbnail"""

    def __init__(self, favorite: bool = False, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._fav = favorite
        self.setText("⭐" if favorite else "")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_favorite(self, fav: bool):
        self._fav = fav
        self.setText("⭐" if fav else "")
