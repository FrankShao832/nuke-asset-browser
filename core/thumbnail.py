"""Nuke Asset Browser — Thumbnail placeholder generation (Phase 1 Mock)"""

from __future__ import annotations

from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics
from PySide6.QtCore import Qt, QRect


# ── Type → color / icon mapping ──
TYPE_STYLE = {
    "template": (QColor("#2d5a8e"), "📄"),    # blue
    "image":    (QColor("#2d8e5a"), "🖼️"),     # green
    "video":    (QColor("#8e2d2d"), "🎬"),     # red
    "script":   (QColor("#6a2d8e"), "📜"),     # purple
    "other":    (QColor("#555555"), "📁"),      # gray
}


def get_placeholder_thumbnail(draft_type: str, size: tuple[int, int] = (260, 180)) -> QPixmap:
    """Generate a colored placeholder thumbnail for a draft type.

    Args:
        draft_type: One of template/image/video/script/other
        size: (width, height) in pixels

    Returns:
        QPixmap with colored background + type icon
    """
    w, h = size
    color, icon = TYPE_STYLE.get(draft_type, TYPE_STYLE["other"])

    pixmap = QPixmap(w, h)
    pixmap.fill(color)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Darker overlay at bottom for text
    overlay_rect = QRect(0, h - 32, w, 32)
    painter.fillRect(overlay_rect, QColor(0, 0, 0, 100))

    # Large icon in center
    font_icon = QFont("Segoe UI Emoji", 42)
    painter.setFont(font_icon)
    painter.setPen(QColor(255, 255, 255, 60))
    painter.drawText(QRect(0, 0, w, h - 32), Qt.AlignCenter, icon)

    # Type label at bottom
    font_label = QFont("Segoe UI", 10)
    painter.setFont(font_label)
    painter.setPen(QColor(255, 255, 255, 180))
    painter.drawText(overlay_rect, Qt.AlignCenter, draft_type.upper())

    painter.end()
    return pixmap


def prewarm_placeholders(cache: dict, size: tuple[int, int] = (260, 180)):
    """Pre-generate all type placeholders into a cache dict."""
    for t in TYPE_STYLE:
        cache[t] = get_placeholder_thumbnail(t, size)


# ── If run directly, show preview ──
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QHBoxLayout

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Thumbnail Placeholder Preview")
    layout = QHBoxLayout(window)

    for t in ("template", "image", "video", "script", "other"):
        pix = get_placeholder_thumbnail(t, (180, 120))
        label = QLabel()
        label.setPixmap(pix)
        label.setToolTip(t)
        layout.addWidget(label)

    window.show()
    sys.exit(app.exec())
