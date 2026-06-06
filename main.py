"""Nuke Asset Browser — Single Entry Point

Three run modes:
  A: python -m asset_browser.main       → Standalone (development)
  B: python asset_browser/main.py       → Same as A (PyCharm friendly)
  C: import asset_browser.main          → Nuke plugin (production)
"""

import sys
import os

# ── Ensure the asset_browser package is discoverable ────────────────────
# When run as a script (mode B), Python adds main.py's directory to
# sys.path, but we need the *parent* directory to resolve "asset_browser"
# as a package.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_PROJECT_ROOT)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

# ── Auto-load the project-local conda env ───────────────────────────────
_ENV_DIR = os.path.join(_PROJECT_ROOT, "env")
_VENV_SITE = os.path.join(_ENV_DIR, "lib", "python3.11", "site-packages")

if os.path.isdir(_VENV_SITE):
    sys.path.insert(0, _VENV_SITE)
else:
    print(f"⚠️  Virtual environment not found: {_ENV_DIR}")
    print(f"   Run: conda create --prefix {_ENV_DIR} python=3.11 pyside6 -c conda-forge")


# ── Mode A/B: Standalone (development) ──────────────────────────────────
def run_standalone() -> None:
    """Launch the browser window as a standalone application"""
    from PySide6.QtWidgets import QApplication
    from asset_browser.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Nuke Asset Browser")
    app.setOrganizationName("VFX Pipeline")

    window = MainWindow()
    window.setWindowTitle("Nuke Asset Browser (Standalone)")
    window.show()

    sys.exit(app.exec())


# ── Mode C: Nuke plugin (production) ────────────────────────────────────
def install_menu() -> None:
    """Register the browser into Nuke's menu"""
    try:
        import nuke
    except ImportError:
        return  # not running inside Nuke

    toolbar = nuke.menu("Nuke").addCommand(
        "Asset Browser/Open Browser",
        "asset_browser.main.open_browser()",
        "^b"  # Ctrl+Shift+B
    )


_windows: dict[str, object] = {}


def open_browser() -> None:
    """Open the browser window (singleton)"""
    from asset_browser.ui.main_window import MainWindow

    key = "__main__"
    if key not in _windows:
        _windows[key] = MainWindow()

    win = _windows[key]
    win.show()
    win.raise_()


# ── Entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_standalone()
