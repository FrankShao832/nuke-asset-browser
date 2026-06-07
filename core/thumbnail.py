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
    "sequence": (QColor("#2d8e5a"), "🎞️"),    # green (same as image)
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
            pix = _load_pixmap_safe(first_frame_path)
            if not pix.isNull():
                logger.debug("Loaded sequence first-frame thumbnail for draft %d", draft.id)
                # Cache it for next time
                _cache_pixmap(draft.id, pix, thumb_cache_dir)
                return pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    # 3. Direct image file
    if _is_image_file(draft.path):
        pix = _load_pixmap_safe(draft.path)
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


def cache_sequence_frames(
    folder: str,
    pattern: str,
    frame_range: str,
    thumb_cache_dir: str,
    max_dim: int = 256,
) -> list[str]:
    """Pre-convert all frames of an image sequence to cached PNG thumbnails.

    Args:
        folder: Folder containing the sequence.
        pattern: e.g. ``"render_%04d.exr"``.
        frame_range: e.g. ``"1001-1048"``.
        thumb_cache_dir: Where to write the cached PNGs.
        max_dim: Maximum dimension for cached thumbnails.

    Returns:
        List of cached PNG file paths (one per frame).
    """
    if "-" not in frame_range:
        return []
    try:
        start, end = int(frame_range.split("-")[0]), int(frame_range.split("-")[1])
    except (ValueError, IndexError):
        return []

    os.makedirs(thumb_cache_dir, exist_ok=True)
    cached: list[str] = []

    for i, f in enumerate(range(start, end + 1)):
        src = os.path.join(folder, pattern % f)
        if not os.path.isfile(src):
            continue
        # Cache name: sequence_{draft_id}_{frame_index}.png
        cache_name = f"seq_{os.path.basename(folder)}_{i:04d}.png"
        cache_path = os.path.join(thumb_cache_dir, cache_name)

        if os.path.isfile(cache_path):
            cached.append(cache_path)
            continue

        pix = _load_pixmap_safe(src)
        if pix.isNull():
            cached.append(src)  # fallback: use source path
            continue

        # Downscale for playback speed
        if pix.width() > max_dim or pix.height() > max_dim:
            pix = pix.scaled(
                max_dim, max_dim, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        ok = pix.save(cache_path, "PNG")
        if ok:
            cached.append(cache_path)
            logger.debug("Cached sequence frame: %s", cache_path)
        else:
            cached.append(src)

    logger.info("Cached %d/%d sequence frames to %s", len(cached), end - start + 1, thumb_cache_dir)
    return cached


# ── Internal helpers ────────────────────────────────────────────────────

def _load_pixmap_safe(path: str) -> QPixmap:
    """Load a pixmap, falling back to OpenEXR/DPX readers if needed."""
    pix = QPixmap(path)
    if not pix.isNull():
        return pix

    # QPixmap failed — try format-specific readers
    ext = os.path.splitext(path)[1].lower()

    if ext == ".exr":
        exr_pix = _load_exr_thumbnail(path)
        if exr_pix and not exr_pix.isNull():
            return exr_pix

    if ext in (".dpx",):
        dpx_pix = _read_dpx_thumbnail(path)
        if dpx_pix and not dpx_pix.isNull():
            return dpx_pix

    logger.debug("Could not load image: %s", path)
    return pix  # null pixmap


def _load_exr_thumbnail(path: str, max_dim: int = 512) -> Optional[QPixmap]:
    """Read an EXR file and return a downsized QPixmap.

    Args:
        path: Path to the .exr file.
        max_dim: Maximum dimension for the thumbnail (preserves aspect).

    Returns:
        QPixmap or ``None`` on failure.
    """
    try:
        import OpenEXR
        import Imath
        import numpy as np
        from PySide6.QtGui import QImage
    except ImportError:
        logger.debug("OpenEXR not available, cannot read %s", path)
        return None

    try:
        exr = OpenEXR.InputFile(path)
        dw = exr.header()["dataWindow"]
        pw, ph = dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1

        # Determine which channels to read (prefer R,G,B)
        header = exr.header()
        chans = header["channels"]
        if "R" in chans and "G" in chans and "B" in chans:
            r_str, g_str, b_str = exr.channels("RGB", Imath.PixelType(Imath.PixelType.FLOAT))
            has_alpha = "A" in chans
            a_str = exr.channel("A", Imath.PixelType(Imath.PixelType.FLOAT)) if has_alpha else None
        elif "r" in chans and "g" in chans and "b" in chans:
            r_str, g_str, b_str = exr.channels("rgb", Imath.PixelType(Imath.PixelType.FLOAT))
            has_alpha = "a" in chans
            a_str = exr.channel("a", Imath.PixelType(Imath.PixelType.FLOAT)) if has_alpha else None
        else:
            logger.debug("EXR %s has no RGB channels", path)
            return None

        # Decode to numpy arrays
        r = np.frombuffer(r_str, dtype=np.float32).reshape(ph, pw)
        g = np.frombuffer(g_str, dtype=np.float32).reshape(ph, pw)
        b = np.frombuffer(b_str, dtype=np.float32).reshape(ph, pw)

        # Downsample to max_dim
        scale = min(max_dim / pw, max_dim / ph, 1.0)
        if scale < 1.0:
            nw = max(1, int(pw * scale))
            nh = max(1, int(ph * scale))
            r = _downsample(r, nw, nh)
            g = _downsample(g, nw, nh)
            b = _downsample(b, nw, nh)
            pw, ph = nw, nh

        # Tone-map: gamma 2.2 only (matches Nuke's Viewer for linear EXR)
        def tonemap(rgb: np.ndarray) -> np.ndarray:
            """Linear → clamp negatives → gamma 2.2 → 8-bit.

            This matches Nuke's Viewer behavior for linear Rec.709/sRGB EXR:
            no auto-exposure, just the standard display gamma.
            """
            rgb = np.maximum(rgb, 0.0)
            arr = np.power(rgb, 1.0 / 2.2)
            np.clip(arr, 0.0, 1.0, out=arr)
            return (arr * 255.0).astype(np.uint8)

        rgb = np.stack((r, g, b), axis=-1)
        rgb_8 = tonemap(rgb)

        # Pack into QImage (RGB888)
        img = QImage(rgb_8.data, pw, ph, pw * 3, QImage.Format_RGB888)
        return QPixmap.fromImage(img)

    except Exception as exc:
        logger.warning("Failed to read EXR thumbnail %s: %s", path, exc)
        return None


def _downsample(arr: np.ndarray, nw: int, nh: int) -> np.ndarray:
    """Simple block-average downsample."""
    import numpy as np
    h, w = arr.shape
    row_factor = h // nh
    col_factor = w // nw
    # Trim to exact multiples
    arr = arr[:nh * row_factor, :nw * col_factor]
    return arr.reshape(nh, row_factor, nw, col_factor).mean(axis=(1, 3))

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


# ── DPX reader ─────────────────────────────────────────────────────────


def _read_dpx_thumbnail(path: str, max_dim: int = 512) -> Optional[QPixmap]:
    """Read a DPX file and return a thumbnail as QPixmap via ffmpeg."""
    import subprocess
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream=width,height",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=15,
        )
        if probe.returncode != 0:
            logger.debug("ffprobe failed for %s", path)
            return None
        parts = probe.stdout.strip().split(",")
        if len(parts) != 2:
            return None
        pw, ph = int(parts[0]), int(parts[1])
        if pw < 1 or ph < 1 or pw > 16384 or ph > 16384:
            return None

        scale = min(max_dim / pw, max_dim / ph, 1.0)
        nw = max(1, int(pw * scale))
        nh = max(1, int(ph * scale))

        proc = subprocess.run(
            ["ffmpeg", "-v", "quiet", "-i", path,
             "-frames:v", "1", "-f", "rawvideo",
             "-pix_fmt", "rgb24", "-s", f"{nw}x{nh}", "-"],
            capture_output=True, timeout=30,
        )
        if proc.returncode != 0:
            return None

        raw = np.frombuffer(proc.stdout, dtype=np.uint8).reshape(nh, nw, 3)
        rgb_f = raw.astype(np.float32) / 255.0
        rgb_f = np.power(rgb_f, 1.0 / 2.2)
        np.clip(rgb_f, 0.0, 1.0, out=rgb_f)
        rgb_8 = (rgb_f * 255.0).astype(np.uint8)

        img = QImage(rgb_8.data, nw, nh, nw * 3, QImage.Format_RGB888)
        return QPixmap.fromImage(img)

    except FileNotFoundError:
        logger.warning("ffmpeg not found — cannot decode DPX: %s", path)
        return None
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg timeout for DPX: %s", path)
        return None
    except Exception as exc:
        logger.warning("Failed to read DPX thumbnail %s: %s", path, exc)
        return None
