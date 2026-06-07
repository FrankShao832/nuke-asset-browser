"""Tests for core/sequence.py — image sequence detection"""

from __future__ import annotations

import os
import tempfile

import pytest

from asset_browser.core.sequence import detect_sequences, detect_from_file, SequenceInfo


def _make_seq(tmpdir: str, basename: str, ext: str, padding: int,
              start: int, end: int) -> None:
    """Create a sequence of empty files in *tmpdir*."""
    for f in range(start, end + 1):
        name = f"{basename}{f:0{padding}d}{ext}"
        open(os.path.join(tmpdir, name), "w").close()


class TestDetectSequences:
    def test_simple_exr(self):
        with tempfile.TemporaryDirectory() as d:
            _make_seq(d, "render_", ".exr", 4, 1001, 1005)
            seqs = detect_sequences(d)
            assert len(seqs) == 1
            s = seqs[0]
            assert s.basename == "render_"
            assert s.pattern == "render_%04d.exr"
            assert s.frame_range_str == "1001-1005"
            assert s.name == "render"

    def test_png_3_pad(self):
        with tempfile.TemporaryDirectory() as d:
            _make_seq(d, "shot_", ".png", 3, 1, 10)
            seqs = detect_sequences(d)
            assert len(seqs) == 1
            assert seqs[0].pattern == "shot_%03d.png"

    def test_multiple_sequences(self):
        with tempfile.TemporaryDirectory() as d:
            _make_seq(d, "fg_", ".exr", 4, 1, 5)
            _make_seq(d, "bg_", ".exr", 4, 1, 3)
            seqs = detect_sequences(d)
            assert len(seqs) == 2

    def test_no_sequence(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "readme.txt"), "w").close()
            open(os.path.join(d, "notes.md"), "w").close()
            assert detect_sequences(d) == []

    def test_non_image_ext_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            _make_seq(d, "data_", ".txt", 4, 1, 3)
            assert detect_sequences(d) == []

    def test_empty_folder(self):
        with tempfile.TemporaryDirectory() as d:
            assert detect_sequences(d) == []

    def test_single_frame_no_padding(self):
        """Files without at least 2 padding digits are ignored."""
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "frame1.exr"), "w").close()  # only 1 digit
            assert detect_sequences(d) == []


class TestDetectFromFile:
    def test_from_middle_frame(self):
        with tempfile.TemporaryDirectory() as d:
            _make_seq(d, "render_", ".exr", 4, 1001, 1010)
            seq = detect_from_file(os.path.join(d, "render_1005.exr"))
            assert seq is not None
            assert seq.frame_range_str == "1001-1010"

    def test_single_file_no_sequence(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "render_0001.exr"), "w").close()
            seq = detect_from_file(os.path.join(d, "render_0001.exr"))
            # Single file with padding is still a valid sequence of length 1
            assert seq is not None
            assert seq.frame_range_str == "1-1"


class TestSequenceInfo:
    def test_frame_path(self):
        s = SequenceInfo("/path", "render_", ".exr", 4, 1001, 1005,
                         frames=list(range(1001, 1006)))
        assert s.first_path() == "/path/render_1001.exr"
        assert s.frame_path(1003) == "/path/render_1003.exr"

    def test_name_strips_trailing_underscore(self):
        s = SequenceInfo("/p", "shot_", ".exr", 4, 1, 10, frames=[])
        assert s.name == "shot"

    def test_name_strips_trailing_dot(self):
        s = SequenceInfo("/p", "comp_v001.", ".exr", 4, 1, 5, frames=[])
        assert s.name == "comp_v001"
