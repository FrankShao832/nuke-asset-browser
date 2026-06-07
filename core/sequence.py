"""Nuke Asset Browser — Image sequence detection

Detects frame sequences inside a folder or infers from a single frame file.

A sequence is a set of files sharing the same base name and extension,
differing only by a zero-padded frame number, e.g.::

    /path/to/render_0001.exr
    /path/to/render_0002.exr
    /path/to/render_0003.exr
    …
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass, field
from typing import Optional

# ── Supported image extensions ──────────────────────────────────────────

_SEQUENCE_EXTS: set[str] = {
    ".exr", ".png", ".jpg", ".jpeg", ".tif", ".tiff",
    ".tga", ".dpx", ".bmp", ".gif", ".webp",
}

# Regex: extract trailing frame number before extension.
# e.g. "render_0001.exr" → ("render_", "0001", ".exr")
_FRAME_RE = re.compile(r"^(.*?)(\d{2,})(\.[a-zA-Z0-9]+)$")


# ── Data ────────────────────────────────────────────────────────────────

@dataclass
class SequenceInfo:
    """Describes a single image sequence inside a folder."""
    folder: str                     # e.g. "/path/to/"
    basename: str                   # e.g. "render_"
    ext: str                        # e.g. ".exr"
    padding: int                    # e.g. 4
    start: int                      # first frame number
    end: int                        # last frame number
    frames: list[int] = field(repr=False, default_factory=list)

    @property
    def pattern(self) -> str:
        """Return the glob-like pattern, e.g. ``render_%04d.exr``."""
        return f"{self.basename}%0{self.padding}d{self.ext}"

    @property
    def name(self) -> str:
        """Human-readable name (basename without trailing ``_`` / ``.``)."""
        return self.basename.rstrip("_.")

    @property
    def frame_range_str(self) -> str:
        """e.g. ``"1001-1048"``."""
        return f"{self.start}-{self.end}"

    def frame_path(self, frame: int) -> str:
        """Full path for a given frame number."""
        return os.path.join(self.folder, self.pattern % frame)

    def first_path(self) -> str:
        """Full path for the first frame."""
        return self.frame_path(self.start)


# ── Detection ───────────────────────────────────────────────────────────

def detect_sequences(folder: str) -> list[SequenceInfo]:
    """Scan *folder* and return all detected frame sequences.

    Returns:
        List of :class:`SequenceInfo` — empty if nothing found.
    """
    if not os.path.isdir(folder):
        return []

    sequences: dict[str, SequenceInfo] = {}

    for fname in os.listdir(folder):
        m = _FRAME_RE.match(fname)
        if not m:
            continue
        base, num_str, ext = m.groups()
        if ext.lower() not in _SEQUENCE_EXTS:
            continue

        key = (base, ext.lower())
        if key not in sequences:
            padding = len(num_str)
            sequences[key] = SequenceInfo(
                folder=folder,
                basename=base,
                ext=ext,
                padding=padding,
                start=int(num_str),
                end=int(num_str),
                frames=[],
            )
        seq = sequences[key]
        frame_n = int(num_str)
        seq.frames.append(frame_n)
        seq.start = min(seq.start, frame_n)
        seq.end = max(seq.end, frame_n)

    # Sort frames in each sequence + ensure padding consistency
    result: list[SequenceInfo] = []
    for seq in sequences.values():
        seq.frames.sort()
        result.append(seq)

    result.sort(key=lambda s: s.basename)
    return result


def detect_from_file(filepath: str) -> Optional[SequenceInfo]:
    """Given a single frame file, infer the sequence it belongs to.

    Scans the parent folder for siblings matching the same pattern.
    Returns ``None`` if the file doesn't look like a sequence frame.
    """
    folder = os.path.dirname(filepath)
    fname = os.path.basename(filepath)

    m = _FRAME_RE.match(fname)
    if not m:
        return None

    sequences = detect_sequences(folder)
    for seq in sequences:
        if seq.basename == m.group(1) and seq.ext.lower() == m.group(3).lower():
            return seq

    return None


def format_nuke_path(folder: str, pattern: str, frame_range: str) -> str:
    """Produce a Nuke-compatible file path, e.g.::

        /path/to/render_%04d.exr 1001-1048
    """
    fname = os.path.join(folder, pattern)
    return f"{fname} {frame_range}"
