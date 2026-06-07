"""Nuke Asset Browser — Transient Toast Notification"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve


class Toast(QWidget):
    """Transient notification pill — auto-fades after duration.

    Floats above all window content. Usage:

        Toast.show(self, "✅ Draft saved", Toast.SUCCESS)
        Toast.show(self, "❌ Delete failed", Toast.ERROR)
        Toast.show(self, "ℹ️ 5 drafts loaded", Toast.INFO)
    """

    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"

    _BG = {
        SUCCESS: "#1a3a1a",
        ERROR: "#3a1a1a",
        INFO: "#1a2a3a",
    }
    _BORDER = {
        SUCCESS: "#2a5a2a",
        ERROR: "#5a2a2a",
        INFO: "#2a3a5a",
    }
    _TEXT = {
        SUCCESS: "#4caf50",
        ERROR: "#ef5350",
        INFO: "#64b5f6",
    }

    def __init__(self, parent: QWidget, message: str,
                 toast_type: str = INFO):
        super().__init__(parent)
        self._toast_type = toast_type
        self.setup_ui(message)
        self.position_and_show()

    def setup_ui(self, message: str):
        bg = self._BG.get(self._toast_type, self._BG[self.INFO])
        border = self._BORDER.get(self._toast_type, self._BORDER[self.INFO])
        text_color = self._TEXT.get(self._toast_type, self._TEXT[self.INFO])

        self.setStyleSheet(f"""
            Toast {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)

        self._label = QLabel(message)
        self._label.setStyleSheet(
            f"color: {text_color}; font-size: 13px; font-weight: 600; "
            f"background: transparent;"
        )
        layout.addWidget(self._label)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Opacity for fade animation
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

    def position_and_show(self):
        parent = self.parent()
        if not parent:
            return

        # Size to content, then position over the status bar if possible
        self.adjustSize()
        tw = self.width()
        th = self.height()
        pw = parent.width()

        # If parent has a _status_bar child, float centered over it
        status_bar = getattr(parent, '_status_bar', None)
        if status_bar and status_bar.isVisible():
            sb = status_bar.geometry()
            x = max(0, (pw - tw) // 2)
            y = sb.y() + (sb.height() - th) // 2
        else:
            # Fallback: float above bottom edge
            x = max(0, (pw - tw) // 2)
            y = parent.height() - th - 40

        self.move(x, y)

        # Raise above all siblings + show as widget
        self.raise_()
        super(Toast, self).show()  # call QWidget.show(), not Toast.show

        # Auto-fade after 2s
        QTimer.singleShot(2000, self.fade_out)

    def fade_out(self):
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(500)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()

    @classmethod
    def appear(cls, parent: QWidget, message: str,
             toast_type: str = INFO) -> "Toast":
        """Create and show a toast on *parent* widget."""
        return cls(parent, message, toast_type)
