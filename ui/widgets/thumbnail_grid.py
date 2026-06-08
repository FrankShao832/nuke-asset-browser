"""Nuke Asset Browser — Thumbnail Grid"""

from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QMenu, QFrame, QLayout, QLayoutItem, QApplication,
)
from PySide6.QtCore import Signal, Qt, QSize, QRect, QPoint, QMimeData, QUrl, QTimer
from PySide6.QtGui import QDrag, QPixmap, QColor

from asset_browser.core.models import Draft
from asset_browser.core.sequence import detect_sequences, detect_from_file
from asset_browser.core.thumbnail import (
    get_thumbnail, invalidate_cache, _load_pixmap_safe,
    _CARD_W, _CARD_H, VIDEO_EXTS, extract_video_frames,
)
from asset_browser.ui.theme import Color, FontSize, Styles
from asset_browser.ui.widgets.draft_badge import DraftBadge, FavoriteStar
from asset_browser.utils.config import config

# ── LRU thumbnail cache (avoids re-reading disk on rebuild/scroll) ─────
_THUMB_CACHE: dict[int, QPixmap] = {}
_MAX_CACHE_SIZE = 200


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

    def __init__(self, draft: Draft, thumbnail=None, thumb_cache_dir=None, parent=None):
        super().__init__(parent)
        self._draft = draft
        self._thumbnail = thumbnail
        self._thumb_cache_dir = thumb_cache_dir
        self._drag_start_pos: QPoint | None = None

        # ── Hover playback for sequences ──
        self._playback_frames: list[str] = []
        self._playback_cache: dict[str, str] = {}  # src → cached PNG path
        self._playback_index = 0
        self._playback_ready = False  # only True once frames are loaded
        self._playback_timer = QTimer(self)
        self._playback_timer.setInterval(42)  # ~24 fps
        self._playback_timer.timeout.connect(self._playback_tick)
        self._init_playback_frames()
        # For video: kick off async frame extraction
        if self._draft.draft_type == "video" and not self._playback_frames:
            from PySide6.QtCore import QTimer as _QTimer
            _QTimer.singleShot(0, self._preload_video_frames)
        self.setFixedSize(200, 160)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(Styles.card())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)

        # Thumbnail area
        card_inner_w = 200 - 12  # 188 (after 6px padding each side)
        thumb_h = 160 - 12 - 40  # 108
        thumb_area = QWidget()
        thumb_area.setFixedHeight(thumb_h)
        thumb_area.setStyleSheet(f"background: {Color.TRANSPARENT}; border: none;")
        thumb_layout = QVBoxLayout(thumb_area)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setSpacing(0)

        self._thumb_label = QLabel()
        self._thumb_label.setAlignment(Qt.AlignCenter)
        self._thumb_label.setFixedHeight(thumb_h)
        # Show placeholder text immediately; real thumbnail loaded lazily
        self._thumb_label.setText("⏳")
        self._thumb_label.setStyleSheet(
            f"color: {Color.TEXT_MUTED}; font-size: 24px;"
        )
        self._thumb_label.setAlignment(Qt.AlignCenter)
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

        self._name_label = QLabel()
        self._name_label.setWordWrap(False)
        # Elide long names with "…"
        self._name_label.setToolTip(draft.name)
        fm = self._name_label.fontMetrics()
        # Available width: 200(card) - 12(layout margins) - 16(info margins) = 172
        elided = fm.elidedText(draft.name, Qt.ElideRight, 172)
        self._name_label.setText(elided)
        self._name_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {Color.TEXT_TITLE};
            background: {Color.TRANSPARENT};
        """)
        info_layout.addWidget(self._name_label)

        meta = QHBoxLayout()
        meta.setSpacing(4)

        type_label = QLabel(draft.draft_type.upper())
        type_label.setStyleSheet(f"""
            font-size: {FontSize.SMALL};
            color: #d4d4d4;
            background: {Color.BTN_NORMAL};
            border-radius: 2px;
            padding: 0 4px;
        """)
        meta.addWidget(type_label)

        author_label = QLabel(f"by {draft.author}")
        author_label.setStyleSheet(Styles.label_small("#bbb"))
        meta.addWidget(author_label)

        meta.addStretch()

        if draft.use_count > 0:
            use_label = QLabel(f"🔥 {draft.use_count}")
            use_label.setStyleSheet(Styles.label_small(Color.TEXT_SMALL))
            meta.addWidget(use_label)

        info_layout.addLayout(meta)
        layout.addWidget(info)

    def _update_thumb(self):
        if self._thumbnail is not None:
            pix = self._thumbnail
        else:
            thumb_dir = self._thumb_cache_dir or config.thumbnail_cache_dir
            pix = get_thumbnail(self._draft, thumb_dir)
        self._thumb_label.setPixmap(
            pix.scaled(_CARD_W, _CARD_H,
                       Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        )

    def set_thumbnail(self, pixmap):
        self._thumbnail = pixmap
        self._update_thumb()

    def refresh_thumbnail(self):
        """Re-resolve thumbnail from storage (bypasses cached pixmap)."""
        self._thumbnail = None
        self._update_thumb()

    def set_favorite(self, fav: bool):
        self._draft.favorite = fav
        self._fav_star.set_favorite(fav)

    def draft_id(self) -> int:
        return self._draft.id

    def load_thumbnail_if_visible(self) -> bool:
        """Load the real thumbnail if this card is in the viewport.

        Returns True if the thumbnail was loaded (or was already loaded).
        """
        # Already loaded with real image?
        if self._thumbnail is not None or self._thumb_label.text() != "⏳":
            return True

        # Check visibility within the scroll area viewport
        scroll = self.parentWidget()
        while scroll and not isinstance(scroll, QScrollArea):
            scroll = scroll.parentWidget()
        if not scroll:
            return False

        viewport = scroll.viewport()
        card_rect = QRect(self.mapTo(viewport, QPoint(0, 0)),
                          self.size())
        if not viewport.rect().intersects(card_rect):
            return False  # not visible yet

        # Load from LRU cache or disk
        did = self._draft.id
        if did in _THUMB_CACHE:
            pix = _THUMB_CACHE[did]
        else:
            thumb_dir = self._thumb_cache_dir or config.thumbnail_cache_dir
            pix = get_thumbnail(self._draft, thumb_dir)
            _THUMB_CACHE[did] = pix
            # Evict if cache too large
            if len(_THUMB_CACHE) > _MAX_CACHE_SIZE:
                oldest = next(iter(_THUMB_CACHE))
                del _THUMB_CACHE[oldest]

        self._thumbnail = pix
        # Clear placeholder text
        self._thumb_label.setText("")
        self._thumb_label.setStyleSheet("")
        self._update_thumb()
        return True

    # ── Hover playback (sequence drafts) ────────────────────────────────

    def _init_playback_frames(self):
        """Pre-compute source frame paths for sequence/video drafts.

        - **Sequence:** enumerates frame files from ``frame_range``.
        - **Video:** extracts evenly-spaced frames via ffmpeg.
        Missing frames are filled with the last valid frame to avoid
        visual jumps during playback.
        """
        # ── Video draft → extract frames via ffmpeg (async) ──
        if self._draft.draft_type == "video":
            # Frames are pre-loaded asynchronously in _preload_video_frames
            return

        # ── Sequence draft → enumerate frame files ──
        if not self._draft.sequence_pattern or not self._draft.frame_range:
            return
        folder = self._draft.path
        pattern = self._draft.sequence_pattern
        fr = self._draft.frame_range
        if not folder or not os.path.isdir(folder) or "-" not in fr:
            return
        try:
            start, end = int(fr.split("-")[0]), int(fr.split("-")[1])
        except (ValueError, IndexError):
            return
        frames: list[str] = []
        last_valid = ""
        for f in range(start, end + 1):
            fp = os.path.join(folder, pattern % f)
            if os.path.isfile(fp):
                frames.append(fp)
                last_valid = fp
            elif last_valid:
                frames.append(last_valid)  # fill gap with previous frame
        self._playback_frames = frames
        if frames:
            self._playback_ready = True

    def _preload_video_frames(self):
        """Asynchronously extract video frames for playback.

        Runs in a deferred QTimer callback so the UI thread isn't blocked
        during card construction.
        """
        # Show loading indicator while ffmpeg works
        self._thumb_label.setText("🎬")
        self._thumb_label.setStyleSheet(
            f"color: {Color.TEXT_MUTED}; font-size: 28px;"
        )
        frames = extract_video_frames(
            self._draft.path, count=30,
            cache_dir=self._thumb_cache_dir,
        )
        self._playback_frames = frames
        if frames:
            self._playback_ready = True
            # Refresh thumbnail with the first frame
            self._thumbnail = None
            self._thumb_label.setText("")
            self._thumb_label.setStyleSheet("")
            self._update_thumb()

    def _playback_tick(self):
        """Advance to the next frame."""
        if not self._playback_frames:
            self._playback_timer.stop()
            return
        self._playback_index = (self._playback_index + 1) % len(self._playback_frames)
        src = self._playback_frames[self._playback_index]

        # Use cached PNG if available, otherwise load & cache
        cached = self._playback_cache.get(src)
        if cached and os.path.isfile(cached):
            pix = QPixmap(cached)
        else:
            pix = _load_pixmap_safe(src)
            if not pix.isNull():
                # Cache as PNG for next time (skip if already a PNG)
                _, ext = os.path.splitext(src)
                if ext.lower() != ".png":
                    cache_dir = self._thumb_cache_dir or config.thumbnail_cache_dir
                    os.makedirs(cache_dir, exist_ok=True)
                    cache_name = f"play_{self._draft.id}_{self._playback_index:04d}.png"
                    cache_path = os.path.join(cache_dir, cache_name)
                    if pix.width() > 256 or pix.height() > 256:
                        pix = pix.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    pix.save(cache_path, "PNG")
                    self._playback_cache[src] = cache_path
                    pix = QPixmap(cache_path)  # reload cached copy

        if not pix.isNull():
            self._thumb_label.setPixmap(
                pix.scaled(188, 108, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            )

    def enterEvent(self, event):
        super().enterEvent(event)
        if self._playback_frames and self._playback_ready:
            self._playback_index = 0
            self._playback_timer.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self._playback_timer.isActive():
            self._playback_timer.stop()
            # Restore static thumbnail
            self._thumbnail = None
            self._thumb_label.setText("")
            self._thumb_label.setStyleSheet("")
            self._update_thumb()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            self.clicked.emit(self._draft.id)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self._drag_start_pos is None:
            super().mouseMoveEvent(event)
            return

        # Start drag if mouse has moved far enough
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime = QMimeData()

        # ── Set MIME data for Nuke Node Graph drop ──
        file_path = self._draft.path
        if file_path:
            from pathlib import Path
            as_posix = Path(file_path).as_posix()
            mime.setUrls([QUrl.fromLocalFile(as_posix)])

            if self._draft.sequence_pattern:
                # Sequence: produce Nuke-friendly "path pattern frame-range"
                nuke_path = os.path.join(
                    as_posix, self._draft.sequence_pattern
                )
                mime.setText(f"{nuke_path} {self._draft.frame_range}")
            else:
                mime.setText(as_posix)

        drag.setMimeData(mime)

        # ── Drag pixmap ──
        pix = self.grab().scaled(160, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        drag.setPixmap(pix)
        drag.setHotSpot(QPoint(pix.width() // 2, pix.height() // 2))

        # Execute drag (modal loop, blocks until drop or cancel)
        drag.exec(Qt.CopyAction)

        self._drag_start_pos = None

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
    draft_dropped = Signal(object)  # Draft — created from drag-drop
    drafts_dropped = Signal(list)   # list[Draft] — batch from multi-file drop
    drop_started = Signal()         # Emitted at start of dropEvent processing

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict[int, ThumbnailCard] = {}
        self._drafts: list[Draft] = []
        self._thumb_cache_dir = config.thumbnail_cache_dir
        self._layout = FlowLayout(spacing=8, margin=8)
        self._next_draft_id = -1  # negative IDs for dropped drafts
        self._pending_urls: list[QUrl] = []  # buffered by dropEvent

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet(Styles.scroll_area())
        self.viewport().setStyleSheet(
            f"background: {Color.PANEL}; border-radius: 6px;"
        )
        self.viewport().setAcceptDrops(True)

        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, False)
        content.setStyleSheet(f"background: {Color.TRANSPARENT};")
        content.setLayout(self._layout)
        self.setWidget(content)

        # ── Empty state placeholder ──
        self._empty_label = QLabel(self)
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {Color.TEXT_MUTED}; font-size: 15px; background: transparent;"
        )
        self._empty_label.hide()

        # ── Lazy load on scroll ──
        self.verticalScrollBar().valueChanged.connect(self._lazy_load_visible)

    def _lazy_load_visible(self):
        """Trigger thumbnail loading for cards currently in the viewport."""
        for card in self._cards.values():
            card.load_thumbnail_if_visible()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep empty label centered
        vp = self.viewport()
        if vp and self._empty_label.isVisible():
            vp_w = vp.width()
            vp_h = vp.height()
            self._empty_label.setFixedSize(vp_w, 40)
            self._empty_label.move(0, (vp_h - 40) // 2)

    def showEvent(self, event):
        super().showEvent(event)
        self._layout.invalidate()
        self.widget().updateGeometry()
        QTimer.singleShot(100, self._lazy_load_visible)

    # ── Drag & Drop (folder / sequence file) ────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        # Defer to next event-loop cycle so the UI can repaint the
        # progress indicator before potentially expensive I/O.
        self._pending_urls = [u for u in urls if u.isLocalFile()]
        self.drop_started.emit()
        QTimer.singleShot(0, self._process_pending_drops)
        event.acceptProposedAction()

    def _process_pending_drops(self):
        """Process URLs saved by *dropEvent* (called via singleShot)."""
        drafts: list[Draft] = []
        for url in self._pending_urls:
            path = url.toLocalFile()
            draft = self._draft_from_drop(path)
            if draft:
                drafts.append(draft)

        if not drafts:
            return
        if len(drafts) == 1:
            self.draft_dropped.emit(drafts[0])
        else:
            self.drafts_dropped.emit(drafts)

        self._pending_urls = []

    def _draft_from_drop(self, path: str) -> Draft | None:
        """Create a Draft from a dropped folder, sequence frame, or video file."""
        import time

        if os.path.isdir(path):
            seqs = detect_sequences(path)
            if not seqs:
                return None
            seq = seqs[0]
            draft_type = "sequence"
        elif os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            # Single video file
            if ext in VIDEO_EXTS:
                name = os.path.splitext(os.path.basename(path))[0]
                draft_id = self._next_draft_id
                self._next_draft_id -= 1
                return Draft(
                    id=draft_id,
                    name=name,
                    draft_type="video",
                    path=path,
                    author="frank",
                    status="draft",
                    description=f"Video: {os.path.basename(path)}",
                    tags=[ext.lstrip(".")],
                    created_at=time.strftime("%Y-%m-%d"),
                    updated_at=time.strftime("%Y-%m-%d"),
                )
            # Try sequence frame detection
            seq = detect_from_file(path)
            if not seq:
                return None
            draft_type = "sequence"
        else:
            return None

        draft_id = self._next_draft_id
        self._next_draft_id -= 1
        draft = Draft(
            id=draft_id,
            name=seq.name,
            draft_type="sequence",
            path=seq.folder,
            author="frank",
            status="draft",
            description=f"Sequence: {seq.pattern} [{seq.frame_range_str}]",
            tags=[seq.ext.lstrip(".")],
            created_at=time.strftime("%Y-%m-%d"),
            updated_at=time.strftime("%Y-%m-%d"),
            frame_range=seq.frame_range_str,
            sequence_pattern=seq.pattern,
        )
        return draft

    def set_drafts(self, drafts: list[Draft]):
        self._drafts = drafts
        self._rebuild()
        has_drafts = len(drafts) > 0
        self._empty_label.setVisible(not has_drafts)
        if not has_drafts:
            # Show meaningful message based on context
            self._empty_label.setText("📭 No drafts found\n\nTry adjusting your search or filters")
            # Need to trigger resizeEvent to center it
            vp = self.viewport()
            if vp:
                vp_w = vp.width()
                vp_h = vp.height()
                self._empty_label.setFixedSize(vp_w, 40)
                self._empty_label.move(0, (vp_h - 40) // 2)

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

        # Lazy load thumbnails for visible cards — immediate + delayed fallback
        self._lazy_load_visible()
        QTimer.singleShot(100, self._lazy_load_visible)

    def _add_card(self, draft: Draft):
        card = ThumbnailCard(draft, thumb_cache_dir=self._thumb_cache_dir)
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
