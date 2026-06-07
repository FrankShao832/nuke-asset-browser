"""Nuke Asset Browser — Nuke API utility functions

Provides Nuke-specific helpers for node selection, export, and import.
All functions are wrapped in try/except for safe use outside Nuke.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional


def _nuke_available() -> bool:
    """Check whether we're running inside Nuke."""
    try:
        import nuke  # noqa: F401
        return True
    except ImportError:
        return False


def get_selected_nodes() -> list:
    """Return all currently selected nodes in the Node Graph.

    Returns:
        List of Nuke Node objects, or empty list if outside Nuke.
    """
    if not _nuke_available():
        return []
    try:
        import nuke
        return list(nuke.selectedNodes())
    except Exception:
        return []


def get_selected_nodes_summary() -> list[dict]:
    """Get a summary dict for each selected node.

    Returns:
        List of dicts with keys: name, class_type, xpos, ypos.
        Empty list if no selection or outside Nuke.
    """
    nodes = get_selected_nodes()
    results = []
    for node in nodes:
        try:
            results.append({
                "name": node.name(),
                "class_type": node.Class(),
                "xpos": node.xpos(),
                "ypos": node.ypos(),
            })
        except Exception:
            continue
    return results


def export_selection_to_nk(filepath: str) -> Optional[str]:
    """Export currently selected nodes directly to a .nk file.

    Uses ``nuke.nodeCopy(path)`` — Nuke's built-in node export —
    which writes only the selected nodes (no Viewer contamination).

    Args:
        filepath: Destination path for the .nk file (e.g. ``/tmp/grade.nk``).

    Returns:
        The filepath on success, ``None`` if no nodes selected or export fails.
    """
    import nuke

    nodes = nuke.selectedNodes()
    if not nodes:
        return None

    # Filter out Viewer nodes so they don't tag along
    content = [n for n in nodes if n.Class() != "Viewer"]
    if not content:
        return None

    # Disable undo for the temporary selection tweaks
    nuke.Undo.disable()
    try:
        # Remember selection state so we can restore it
        orig_names = [n.fullName() for n in nodes]
        was_selected = {n.fullName(): True for n in nodes}

        # Restrict selection to content-only (no Viewers)
        for n in nodes:
            n["selected"].setValue(n.fullName() in was_selected and n.Class() != "Viewer")

        # ── Nuke's built-in export: selected nodes → .nk file ──────
        nuke.nodeCopy(filepath)

        # Restore original selection exactly
        for n in nuke.allNodes():
            n["selected"].setValue(n.fullName() in was_selected)

        return filepath if os.path.isfile(filepath) else None

    except Exception:
        import traceback
        traceback.print_exc()
        return None
    finally:
        nuke.Undo.enable()


def get_template_dir() -> str:
    """Get the persistent directory for exported .nk templates.

    Delegates to ``asset_browser.utils.config.config.template_dir``,
    which supports ``AM_TEMPLATE_DIR`` env var override.

    Returns:
        Path to the template directory (created if missing).
    """
    from asset_browser.utils.config import config
    path = config.template_dir
    os.makedirs(path, exist_ok=True)
    return path


def generate_template_name(nodes: list) -> str:
    """Generate a human-readable template name from selected nodes.

    Args:
        nodes: List of Nuke Node objects.

    Returns:
        A snake_case name, e.g. 'grade_blur_merge'.
    """
    names = []
    for node in nodes[:4]:
        try:
            names.append(node.name().lower().replace(" ", "_"))
        except Exception:
            continue

    if not names:
        return "untitled"

    name = "_".join(names)
    if len(nodes) > 4:
        name += f"_plus{len(nodes) - 4}"

    return name
