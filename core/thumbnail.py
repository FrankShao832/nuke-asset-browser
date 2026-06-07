"""Nuke Asset Browser — Thumbnail resolution & caching

Resolution priority for ``get_thumbnail()``:

1. **Explicit thumb path** — ``draft.thumbnail_path`` (user-set or
   auto-generated)
2. **Cached thumbnail** — ``<thumb_cache_dir>/<draft_id>.png``
3. **Direct image load** — if ``draft.path`` points to a readable image
   file (EXR, PNG, JPEG, TIFF, TGA, DPX, …), load and cache it
4. **Placeholder** — colored placeholder based on ``draft.draft_type``
"""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QRect

from asset_browser.core.models import Draft
from asset_browser.utils.logger import get_logger

logger = get_logger(__name__)

# ── Constants ────────────────────────────────────────────────────────────

_CARD_W, _CARD_H = 200, 108  # thumbnail area inside ThumbnailCard

# Extensions QPixmap can load directly (via Qt image-format plugins).
# EXR support requires the ``exr`` Qt plugin (shipped with Nuke's Qt).
_IMAGE_EXTS: set[str] = {
    ".exr", ".png", ".jpg", ".jpeg", ".tif", ".tiff",
    ".tga", ".dpx", ".bmp", ".gif", ".webp", ".svg",
}

# ── Placeholder (fallback) ──────────────────────────────────────────────

_TYPE_STYLE: dict[str, tuple[QColor, str]] = {
    "template": (QColor("#2d5a8e"), "📄"),   # blue
    "image":    (QColor("#2d8e5a"), "🖼️"),    # green
    "video":    (QColor("#8e2d2d"), "🎬"),    # red
    "script":   (QColor("#6a2d8e"), "📜"),    # purple
    "other":    (QColor("#555555"), "📁"),     # gray
}


def _make_placeholder(draft_type: str, w: int, h: int) -> QPixmap:
    """Create a coloured placeholder pixmap for the given type."""
    color, icon = _TYPE_STYLE.get(draft_type, _TYPE_STYLE["other"])
    pix = QPixmap(w, h)
    pix.fill(color)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # Semi-transparent overlay at bottom
    p.fillRect(QRect(0, h - 28, w, 28), QColor(0, 0, 0, 80))

    # Large icon
    f = QFont("Segoe UI Emoji", 36)
    p.setFont(f)
    p.setPen(QColor(255, 255, 255, 60))
    p.drawText(QRect(0, 0, w, h - 28), Qt.AlignCenter, icon)

    p.end()
    return pix


# ── Public API ──────────────────────────────────────────────────────────

def get_thumbnail(
    draft: Draft,
    thumb_cache_dir: str,
    size: tuple[int, int] = (_CARD_W, _CARD_H),
) -> QPixmap:
    """Return the best available thumbnail for *draft*.

    Args:
        draft: The draft to get a thumbnail for.
        thumb_cache_dir: Directory where cached thumbnails live.
        size: Desired (width, height) in pixels.

    Returns:
        A QPixmap — never ``None`` or invalid.
    """
    w, h = size

    # 1. Explicit thumbnail path
    if draft.thumbnail_path:
        pix = QPixmap(draft.thumbnail_path)
        if not pix.isNull():
            logger.debug("Loaded explicit thumbnail for draft %d", draft.id)
            return pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    # 2. Cached thumbnail file
    cached_path = _cached_path(draft.id, thumb_cache_dir)
    if cached_path:
        pix = QPixmap(cached_path)
        if not pix.isNull():
            logger.debug("Loaded cached thumbnail for draft %d", draft.id)
            return pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    # 2b. Sequence draft — load the first frame
    if draft.sequence_pattern:
        first_frame_path = _sequence_first_frame(draft)
        if first_frame_path and _is_image_file(first_frame_path):
            pix = QPixmap(first_frame_path)
            if not pix.isNull():
                logger.debug("Loaded sequence first-frame thumbnail for draft %d", draft.id)
                # Cache it for next time
                _cache_pixmap(draft.id, pix, thumb_cache_dir)
                return pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    # 3. Direct image file
    if _is_image_file(draft.path):
        pix = QPixmap(draft.path)
        if not pix.isNull():
            logger.debug("Loaded image thumbnail from %s", draft.path)
            # Cache it for next time
            _cache_pixmap(draft.id, pix, thumb_cache_dir)
            return pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    # 4. Fallback — colour placeholder
    logger.debug("Placeholder for draft %d (%s)", draft.id, draft.draft_type)
    return _make_placeholder(draft.draft_type, w, h)


def cache_thumbnail(
    draft_id: int,
    source_pixmap: QPixmap,
    thumb_cache_dir: str,
) -> Optional[str]:
    """Save a pixmap as the cached thumbnail for *draft_id*.

    Args:
        draft_id: The numeric draft id.
        source_pixmap: The pixmap to cache.
        thumb_cache_dir: Cache directory.

    Returns:
        Path to the saved file, or ``None`` on failure.
    """
    return _cache_pixmap(draft_id, source_pixmap, thumb_cache_dir)


def cache_image_as_thumbnail(
    draft_id: int,
    source_path: str,
    thumb_cache_dir: str,
) -> Optional[str]:
    """Load an image file and cache it as the thumbnail for *draft_id*.

    Args:
        draft_id: The numeric draft id.
        source_path: Path to a readable image file.
        thumb_cache_dir: Cache directory.

    Returns:
        Path to the saved thumbnail, or ``None`` on failure.
    """
    pix = QPixmap(source_path)
    if pix.isNull():
        logger.warning("Cannot load image for thumbnail: %s", source_path)
        return None
    return _cache_pixmap(draft_id, pix, thumb_cache_dir)


def invalidate_cache(draft_id: int, thumb_cache_dir: str) -> None:
    """Remove the cached thumbnail for *draft_id* (e.g. after deletion)."""
    path = os.path.join(thumb_cache_dir, f"{draft_id}.png")
    try:
        if os.path.isfile(path):
            os.remove(path)
            logger.debug("Removed cached thumbnail: %s", path)
    except OSError as exc:
        logger.warning("Failed to remove cached thumbnail %s: %s", path, exc)


# ── Internal helpers ────────────────────────────────────────────────────

def _is_image_file(path: str) -> bool:
    """Return True if *path* looks like a readable image file."""
    ext = os.path.splitext(path)[1].lower()
    return ext in _IMAGE_EXTS and os.path.isfile(path)


def _cached_path(draft_id: int, thumb_cache_dir: str) -> Optional[str]:
    """Return the path to the cached thumbnail for *draft_id* if it exists."""
    path = os.path.join(thumb_cache_dir, f"{draft_id}.png")
    return path if os.path.isfile(path) else None


def _cache_pixmap(
    draft_id: int,
    pixmap: QPixmap,
    thumb_cache_dir: str,
) -> Optional[str]:
    """Write *pixmap* as ``<thumb_cache_dir>/<draft_id>.png``."""
    try:
        os.makedirs(thumb_cache_dir, exist_ok=True)
        path = os.path.join(thumb_cache_dir, f"{draft_id}.png")
        ok = pixmap.save(path, "PNG")
        if ok:
            logger.debug("Cached thumbnail: %s", path)
            return path
        logger.warning("Failed to save thumbnail: %s", path)
        return None
    except Exception as exc:
        logger.warning("Error caching thumbnail for draft %d: %s", draft_id, exc)
        return None


def _sequence_first_frame(draft: Draft) -> Optional[str]:
    """Return the path to the first frame of a sequence draft."""
    folder = draft.path
    if not folder or not os.path.isdir(folder):
        return None

    # Reconstruct first frame from pattern & frame_range
    pattern = draft.sequence_pattern
    fr = draft.frame_range
    if pattern and fr and "-" in fr:
        try:
            start = int(fr.split("-")[0])
            fname = pattern % start
        except (ValueError, TypeError):
            return None
        path = os.path.join(folder, fname)
        if os.path.isfile(path):
            return path

    # Fallback: scan folder for any sequence
    from asset_browser.core.sequence import detect_sequences
    seqs = detect_sequences(folder)
    if seqs:
        return seqs[0].first_path()
    return None
