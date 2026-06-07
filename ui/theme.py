"""Theme constants and QSS snippets for Asset Browser.

Usage:
    from ui.theme import Color, FontSize, Styles

    label.setStyleSheet(f"color: {Color.TEXT_TITLE}; font-size: {FontSize.TITLE};")
    widget.setStyleSheet(Styles.card())
"""


class Color:
    """Centralized color palette — single source of truth for all UI colors.

    Background hierarchy (lightest → darkest):
        WINDOW > SURFACE > PANEL
    """

    # ── Background ──
    WINDOW = "#2b2b2b"       # Main window, dialog base, card normal
    SURFACE = "#242424"      # Dialog body (slightly darker than window)
    PANEL = "#1e1e1e"        # Sidebar, scroll area, input fields
    CARD_HOVER = "#2d2d2d"   # Thumbnail card hover state

    # ── Button ──
    BTN_NORMAL = "#333"
    BTN_HOVER = "#3a3a3a"
    BTN_PRESSED = "#444"
    BTN_DISABLED = "#888"

    # ── Accent (Blue) ──
    ACCENT = "#3a7bd5"         # Primary action, active state, selection
    ACCENT_HOVER = "#4a8be5"
    ACCENT_PRESSED = "#2a6bc5"

    # ── Border ──
    BORDER = "#3a3a3a"
    BORDER_HOVER = "#444"
    BORDER_ACCENT = "#3a7bd5"

    # ── Text ──
    TEXT_PRIMARY = "#d4d4d4"
    TEXT_TITLE = "#fff"
    TEXT_SECONDARY = "#ccc"
    TEXT_MUTED = "#999"
    TEXT_SMALL = "#666"

    # ── Special ──
    TRANSPARENT = "transparent"
    SUCCESS_BG = "#2a5a2a"
    SUCCESS_BG_HOVER = "#3a6a3a"


class FontSize:
    """Centralized font size constants."""

    TITLE = "16px"
    TAB = "15px"
    BODY = "14px"
    SMALL = "9px"
    BUTTON = "13px"


class Styles:
    """Factory for reusable QSS snippet strings.

    Each classmethod returns a complete QSS block ready for setStyleSheet().
    """

    @classmethod
    def card(cls) -> str:
        """Default thumbnail card."""
        return f"""
            ThumbnailCard {{
                background-color: {Color.WINDOW};
                border: 1px solid {Color.BORDER};
                border-radius: 6px;
            }}
            ThumbnailCard:hover {{
                background-color: {Color.CARD_HOVER};
                border: 1px solid {Color.BORDER_ACCENT};
            }}
        """

    @classmethod
    def primary_button(cls, *, bg: str = "", hover: str = "",
                        pressed: str = "") -> str:
        """Blue accent button (save, apply, upload)."""
        bg = bg or Color.ACCENT
        hover = hover or Color.ACCENT_HOVER
        pressed = pressed or Color.ACCENT_PRESSED
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {Color.TEXT_TITLE};
                border: none;
                border-radius: 6px;
                padding: 6px 24px;
                font-size: {FontSize.BUTTON};
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
        """

    @classmethod
    def secondary_button(cls) -> str:
        """Grey button (cancel, close)."""
        return f"""
            QPushButton {{
                background-color: {Color.BTN_NORMAL};
                color: {Color.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 6px 24px;
                font-size: {FontSize.BUTTON};
            }}
            QPushButton:hover {{
                background-color: {Color.BTN_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Color.BTN_PRESSED};
            }}
        """

    @classmethod
    def icon_button(cls) -> str:
        """Circular/tool button for icons (e.g. settings ⚙️)."""
        return f"""
            QPushButton {{
                border: none;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: {Color.BTN_NORMAL};
                border-radius: 4px;
            }}
        """

    @classmethod
    def input_field(cls, *, error: bool = False) -> str:
        """Text input / QLineEdit."""
        border_color = "#e04e4e" if error else Color.BORDER
        return f"""
            QLineEdit {{
                background-color: {Color.PANEL};
                color: {Color.TEXT_PRIMARY};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: {FontSize.BODY};
                selection-background-color: {Color.ACCENT};
            }}
            QLineEdit:focus {{
                border: 1px solid {Color.BORDER_ACCENT};
            }}
        """

    @classmethod
    def scroll_area(cls) -> str:
        """Scroll area with transparent viewport."""
        return f"""
            QScrollArea {{
                border: none;
                background: {Color.PANEL};
                border-radius: 6px;
            }}
            QScrollArea > QWidget > QWidget {{
                background: {Color.PANEL};
            }}
        """

    @classmethod
    def scroll_bar(cls) -> str:
        """Custom dark scrollbar."""
        return f"""
            QScrollBar:vertical {{
                background: {Color.PANEL};
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {Color.BORDER};
                min-height: 30px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Color.BORDER_HOVER};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: {Color.PANEL};
                height: 8px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {Color.BORDER};
                min-width: 30px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {Color.BORDER_HOVER};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
        """

    @classmethod
    def tab_widget(cls) -> str:
        """QTabWidget with bordered pane."""
        return f"""
            QTabWidget::pane {{
                background: transparent;
                border: 1px solid {Color.BORDER};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background: {Color.BTN_NORMAL};
                color: {Color.TEXT_PRIMARY};
                border: none;
                padding: 6px 16px;
                margin-right: 2px;
                font-size: {FontSize.TAB};
            }}
            QTabBar::tab:selected {{
                background: {Color.ACCENT};
                color: {Color.TEXT_TITLE};
                font-weight: 700;
            }}
            QTabBar::tab:hover:!selected {{
                background: {Color.BTN_HOVER};
            }}
        """

    @classmethod
    def group_box(cls) -> str:
        """QGroupBox with accent title."""
        return f"""
            QGroupBox {{
                font-size: {FontSize.TAB};
                font-weight: 700;
                color: {Color.TEXT_TITLE};
                border: 1px solid {Color.BORDER};
                border-radius: 6px;
                margin-top: 12px;
                padding: 16px 12px 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
        """

    @classmethod
    def label_title(cls) -> str:
        """Bold title label."""
        return f"font-size: {FontSize.TITLE}; font-weight: 700; color: {Color.TEXT_TITLE};"

    @classmethod
    def label_small(cls, color: str = "") -> str:
        """Small muted label."""
        color = color or Color.TEXT_SMALL
        return f"font-size: {FontSize.SMALL}; color: {color}; background: transparent;"


# ── Master stylesheet for QApplication ──

def master_stylesheet() -> str:
    """Global stylesheet applied to the entire application."""
    return f"""
        QWidget {{
            font-size: {FontSize.BODY};
            color: {Color.TEXT_PRIMARY};
            background-color: {Color.WINDOW};
        }}

        QToolTip {{
            background-color: {Color.PANEL};
            color: {Color.TEXT_PRIMARY};
            border: 1px solid {Color.BORDER};
            border-radius: 4px;
            padding: 4px 8px;
            font-size: {FontSize.BODY};
        }}

        QComboBox {{
            background-color: {Color.PANEL};
            color: {Color.TEXT_PRIMARY};
            border: 1px solid {Color.BORDER};
            border-radius: 6px;
            padding: 4px 8px;
            font-size: {FontSize.BODY};
        }}
        QComboBox:hover {{
            border: 1px solid {Color.BORDER_HOVER};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {Color.PANEL};
            color: {Color.TEXT_PRIMARY};
            selection-background-color: {Color.ACCENT};
            border: 1px solid {Color.BORDER};
            outline: none;
        }}

        QCheckBox {{
            color: {Color.TEXT_PRIMARY};
            font-size: {FontSize.BODY};
        }}
        QCheckBox::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid {Color.BORDER};
            border-radius: 3px;
            background: {Color.PANEL};
        }}
        QCheckBox::indicator:checked {{
            background: {Color.ACCENT};
            border: 1px solid {Color.ACCENT};
        }}

        QProgressBar {{
            background-color: {Color.PANEL};
            border: none;
            border-radius: 4px;
            text-align: center;
            color: {Color.TEXT_PRIMARY};
            font-size: {FontSize.SMALL};
            height: 12px;
        }}
        QProgressBar::chunk {{
            background-color: {Color.ACCENT};
            border-radius: 4px;
        }}
    """
