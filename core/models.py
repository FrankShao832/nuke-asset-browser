"""Nuke Asset Browser — Core types & data model"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Draft:
    """A single draft in the asset browser"""
    id: int
    name: str
    draft_type: str  # template / image / video / script / other
    path: str
    author: str = "frank"
    status: str = "draft"          # draft / published / modified
    visibility: str = "private"    # private / shared
    favorite: bool = False
    description: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = "2026-06-05"
    updated_at: str = "2026-06-05"
    thumbnail_path: str = ""
    use_count: int = 0
    frame_range: str = ""               # e.g. "1001-1048"
    sequence_pattern: str = ""          # e.g. "render_%04d.exr"


# ── Mock data ──

MOCK_DRAFTS: list[Draft] = [
    Draft(1,  "film_grain_001",    "template", "/tools/film_grain_001.nk",           "frank",   status="published", created_at="2026-06-05", tags=["grain", "film", "noise"], favorite=True, use_count=42),
    Draft(2,  "light_warp_02",     "image",   "/tools/light_warp/gizmo.nk",          "frank",   status="draft",     created_at="2026-06-04", tags=["light", "warp", "distort"], use_count=18),
    Draft(3,  "dust_sparks",       "video",   "/tools/dust_sparks_v02.nk",            "alice",   status="published", created_at="2026-06-04", tags=["dust", "sparks", "practical"], favorite=True, use_count=67),
    Draft(4,  "color_lut_02",      "template", "/tools/color/lut_02.nk",              "frank",   status="modified",  created_at="2026-06-03", tags=["color", "lut", "grade"], use_count=23),
    Draft(5,  "batch_render",      "script",  "/tools/batch_render_v3.py",            "bob",     status="published", created_at="2026-06-02", tags=["batch", "render", "farm"], use_count=104),
    Draft(6,  "chromatic_shift",   "image",   "/tools/chromatic_shift.nk",            "alice",   status="draft",     created_at="2026-06-02", tags=["chromatic", "abberation", "lens"], use_count=5),
    Draft(7,  "motion_blur_ui",    "template", "/tools/motion_blur_ui_v2.nk",         "frank",   status="published", created_at="2026-06-01", tags=["motion", "blur", "ui"], use_count=31),
    Draft(8,  "glow_rim",          "image",   "/tools/glow/rim_light.nk",             "bob",     status="modified",  created_at="2026-05-30", tags=["glow", "rim", "light"], use_count=12),
    Draft(9,  "keylight_cleanup",  "template", "/tools/key/keylight_clean.nk",        "frank",   status="draft",     created_at="2026-05-28", tags=["keying", "cleanup", "spill"], use_count=7),
    Draft(10, "depth_of_field",    "template", "/tools/dof/dof_v3.nk",                "alice",   status="published", created_at="2026-05-25", tags=["dof", "depth", "bokeh"], favorite=True, use_count=89),
    Draft(11, "lens_flare_kit",    "image",   "/tools/lens/flare_kit.nk",             "frank",   status="draft",     created_at="2026-05-22", tags=["lens", "flare", "optical"], use_count=3),
    Draft(12, "denoise_opt",       "script",  "/tools/denoise/opt.py",                "bob",     status="published", created_at="2026-05-20", tags=["denoise", "opt", "ml"], use_count=45),
    Draft(13, "edge_detect",       "image",   "/tools/edge/edge_detect.nk",           "alice",   status="draft",     created_at="2026-05-18", tags=["edge", "detect", "matte"], use_count=9),
    Draft(14, "pixel_sort",        "image",   "/tools/pixel/pixel_sort.nk",           "frank",   status="published", created_at="2026-05-15", tags=["pixel", "sort", "glitch"], use_count=27),
    Draft(15, "shaker",            "template", "/tools/shake/shaker_v1.nk",           "bob",     status="draft",     created_at="2026-05-12", tags=["shake", "camera", "handheld"], use_count=14),
    Draft(16, "color_match",       "image",   "/tools/color/color_match.nk",          "alice",   status="published", created_at="2026-05-10", tags=["color", "match", "reference"], favorite=True, use_count=56),
    Draft(17, "stabilize_pro",     "template", "/tools/stab/stabilize_pro.nk",        "frank",   status="modified",  created_at="2026-05-08", tags=["stabilize", "track", "pro"], use_count=21),
    Draft(18, "particle_dust",     "video",   "/tools/particle/dust_v2.nk",           "bob",     status="draft",     created_at="2026-05-05", tags=["particle", "dust", "atmosphere"], use_count=6),
    Draft(19, "film_damage_kit",   "template", "/tools/film_damage_kit.nk",           "alice",   status="draft",     created_at="2026-06-01", tags=["film", "damage", "scratch"], use_count=11),
    Draft(20, "batch_export",      "script",  "/tools/batch_export.py",               "frank",   status="published", created_at="2026-05-10", tags=["batch", "export", "render"], use_count=73),
]
