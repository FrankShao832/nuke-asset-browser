"""Nuke Asset Browser — Thumbnail Grid (naked)"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QMenu, QFrame, QLayout, QLayoutItem,
)
from PySide6.QtCore import Signal, Qt, QSize, QRect, QPoint

from asset_browser.core.models import Draft
from asset_browser.core.thumbnail import get_placeholder_thumbnail
from asset_browser.ui.widgets.draft_badge import DraftBadge, FavoriteStar


class FlowLayout(QLayout):
    """Horizontal-flow layout that wraps at container width"""

    def __init__(self, parent=None, margin=0, spacing=6):
        self._items: list[QLayoutItem] = []
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def __del__(self):
        if hasattr(self, '_items'):
            while self._items:
                item = self._items.pop()
                if item.widget():
                    item.widget().deleteLater()

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Horizontal)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def sizeHint(self):
        return QSize(200, 200)

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect)

    def invalidate(self):
        super().invalidate()
        # Reset item geometries so next setGeometry repositions from scratch
        for item in self._items:
            if item.widget():
                item.widget().setGeometry(QRect(-9999, -9999, 0, 0))

    def _do_layout(self, rect, test_only=False):
        m = self.contentsMargins()
        space_x = self.spacing()
        space_y = self.spacing()
        card_w = 200
        card_h = 160

        content_width = rect.width() - m.left() - m.right()
        if content_width <= 0:
            return 0

        # How many cards fit per row
        items_per_row = max(1, (content_width + space_x) // (card_w + space_x))

        visible = [item for item in self._items
                   if item.widget() and item.widget().isVisible()]

        y = rect.y() + m.top()
        i = 0
        while i < len(visible):
            # Collect this row
            row_items = visible[i:i + items_per_row]
            n = len(row_items)
            row_width = n * card_w + (n - 1) * space_x
            x_start = rect.x() + m.left() + (content_width - row_width) // 2

            x = x_start
            for item in row_items:
                if not test_only:
                    item.setGeometry(QRect(x, y, card_w, card_h))
                x += card_w + space_x

            y += card_h + space_y
            i += n

        total_height = y + m.bottom() - rect.y()
        return total_height if test_only else None


class ThumbnailCard(QFrame):
    """Single draft card in the thumbnail grid"""

    clicked = Signal(int)
    double_clicked = Signal(int)
    context_requested = Signal(int, QPoint)

    def __init__(self, draft: Draft, thumbnail=None, parent=None):
        super().__init__(parent)
        self._draft = draft
        self._thumbnail = thumbnail
        self.setFixedSize(200, 160)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            ThumbnailCard {
                background-color: #2b2b2b;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
            ThumbnailCard:hover {
                border: 1px solid #3a7bd5;
                background-color: #2d2d2d;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)

        # Thumbnail area
        card_inner_w = 200 - 12  # 188 (after 6px padding each side)
        thumb_h = 160 - 12 - 40  # 108
        thumb_area = QWidget()
        thumb_area.setFixedHeight(thumb_h)
        thumb_area.setStyleSheet("background: transparent; border: none;")
        thumb_layout = QVBoxLayout(thumb_area)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setSpacing(0)

        self._thumb_label = QLabel()
        self._thumb_label.setAlignment(Qt.AlignCenter)
        self._thumb_label.setFixedHeight(thumb_h)
        self._update_thumb()
        thumb_layout.addWidget(self._thumb_label)

        overlay = QWidget(thumb_area)
        overlay.setGeometry(0, 0, card_inner_w, thumb_h)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        overlay_layout = QHBoxLayout(overlay)
        overlay_layout.setContentsMargins(6, 6, 6, 6)
        overlay_layout.setSpacing(0)

        self._fav_star = FavoriteStar(draft.favorite)
        overlay_layout.addWidget(self._fav_star, alignment=Qt.AlignLeft | Qt.AlignTop)
        overlay_layout.addStretch()
        self._status_badge = DraftBadge(draft.status)
        overlay_layout.addWidget(self._status_badge, alignment=Qt.AlignRight | Qt.AlignTop)

        layout.addWidget(thumb_area)

        # Info area
        info = QWidget()
        info.setFixedHeight(40)
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(1)

        self._name_label = QLabel(draft.name)
        self._name_label.setWordWrap(False)
        self._name_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #ddd;
            background: transparent;
        """)
        info_layout.addWidget(self._name_label)

        meta = QHBoxLayout()
        meta.setSpacing(4)

        type_label = QLabel(draft.draft_type.upper())
        type_label.setStyleSheet("""
            font-size: 9px;
            color: #888;
            background: #333;
            border-radius: 2px;
            padding: 0 4px;
        """)
        meta.addWidget(type_label)

        author_label = QLabel(f"by {draft.author}")
        author_label.setStyleSheet("font-size: 9px; color: #666; background: transparent;")
        meta.addWidget(author_label)

        meta.addStretch()

        if draft.use_count > 0:
            use_label = QLabel(f"🔥 {draft.use_count}")
            use_label.setStyleSheet("font-size: 9px; color: #666; background: transparent;")
            meta.addWidget(use_label)

        info_layout.addLayout(meta)
        layout.addWidget(info)

    def _update_thumb(self):
        if self._thumbnail:
            pix = self._thumbnail
        else:
            pix = get_placeholder_thumbnail(self._draft.draft_type, (200, 120))
        self._thumb_label.setPixmap(pix.scaled(200, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))

    def set_thumbnail(self, pixmap):
        self._thumbnail = pixmap
        self._update_thumb()

    def set_favorite(self, fav: bool):
        self._draft.favorite = fav
        self._fav_star.set_favorite(fav)

    def draft_id(self) -> int:
        return self._draft.id

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._draft.id)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self._draft.id)

    def contextMenuEvent(self, event):
        self.context_requested.emit(self._draft.id, event.globalPos())


class ThumbnailGrid(QScrollArea):
    """Grid of draft thumbnail cards with context menu"""

    draft_selected = Signal(int)
    draft_activated = Signal(int)
    favorite_toggled = Signal(int, bool)
    delete_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict[int, ThumbnailCard] = {}
        self._drafts: list[Draft] = []
        self._layout = FlowLayout(spacing=8, margin=8)

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("""
            QScrollArea { border-radius: 6px; background: #1e1e1e; }
            QScrollArea > QWidget > QWidget { background: #1e1e1e; }
        """)
        self.viewport().setStyleSheet("background: #1e1e1e; border-radius: 6px;")

        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, False)
        content.setStyleSheet("background: transparent;")
        content.setLayout(self._layout)
        self.setWidget(content)

    def showEvent(self, event):
        super().showEvent(event)
        self._layout.invalidate()
        self.widget().updateGeometry()

    def set_drafts(self, drafts: list[Draft]):
        self._drafts = drafts
        self._rebuild()

    def add_draft(self, draft: Draft):
        self._drafts.append(draft)
        self._add_card(draft)

    def remove_draft(self, draft_id: int):
        self._drafts = [d for d in self._drafts if d.id != draft_id]
        card = self._cards.pop(draft_id, None)
        if card:
            self._layout.removeWidget(card)
            card.deleteLater()

    def _rebuild(self):
        # Full teardown: replace the content widget entirely
        # This avoids stale layout state from add/remove cycles
        old = self.takeWidget()
        if old:
            old.deleteLater()

        self._cards.clear()
        self._layout = FlowLayout(spacing=8, margin=8)

        for draft in self._drafts:
            self._add_card(draft)

        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, False)
        content.setStyleSheet("background: transparent;")
        content.setLayout(self._layout)
        self.setWidget(content)

        # Immediately force layout with the correct viewport width
        vp_w = self.viewport().width() if self.viewport() else 200
        if vp_w > 0:
            content.resize(vp_w, content.height())
            self._layout.setGeometry(QRect(0, 0, vp_w, content.height()))

    def _add_card(self, draft: Draft):
        card = ThumbnailCard(draft)
        card.clicked.connect(lambda did: self.draft_selected.emit(did))
        card.double_clicked.connect(lambda did: self.draft_activated.emit(did))
        card.context_requested.connect(self._show_context_menu)
        self._cards[draft.id] = card
        self._layout.addWidget(card)

    def _show_context_menu(self, draft_id: int, pos: QPoint):
        draft = next((d for d in self._drafts if d.id == draft_id), None)
        if not draft:
            return

        menu = QMenu(self)

        fav_text = "⭐ Unfavorite" if draft.favorite else "⭐ Favorite"
        fav_action = menu.addAction(fav_text)
        fav_action.triggered.connect(lambda: self._toggle_favorite(draft_id))

        menu.addSeparator()
        menu.addAction("📤 Publish to Asset Manager").setEnabled(False)
        menu.addAction("✏️ Rename").setEnabled(False)
        menu.addSeparator()
        menu.addAction("📋 Copy Path").triggered.connect(lambda: self._copy_path(draft))
        menu.addAction("📂 Open Containing Folder").setEnabled(False)
        menu.addSeparator()
        del_action = menu.addAction("🗑️ Delete")
        del_action.triggered.connect(lambda: self.delete_requested.emit(draft_id))

        menu.exec(pos)

    def _toggle_favorite(self, draft_id: int):
        card = self._cards.get(draft_id)
        draft = next((d for d in self._drafts if d.id == draft_id), None)
        if card and draft:
            new_state = not draft.favorite
            card.set_favorite(new_state)
            draft.favorite = new_state
            self.favorite_toggled.emit(draft_id, new_state)

    @staticmethod
    def _copy_path(draft: Draft):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(draft.path)
