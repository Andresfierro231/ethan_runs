"""Tests for the reusable figure toolkit and palette validator (AGENT-234)."""

from __future__ import annotations

import re
from pathlib import Path

import palette_validator
import svg_chart_kit as kit


# ── palette_validator ──────────────────────────────────────────────────────────
def test_validator_passes_project_palette() -> None:
    result = palette_validator.validate(["#2a78d6", "#eb6834", "#4a3aa7", "#008300"])
    assert result["ok"] is True
    assert result["worst_cvd"] >= 12.0


def test_validator_flags_low_chroma_gray() -> None:
    # two near-grays should fail the chroma floor
    result = palette_validator.validate(["#808080", "#888888"])
    states = {name: state for name, state, _ in result["report"]}
    assert states["Chroma floor"] == "FAIL"
    assert result["ok"] is False


def test_validator_contrast_matches_wcag() -> None:
    # white on white ~ 1:1
    assert palette_validator.contrast("#ffffff", "#ffffff") == 1.0
    # black on white = 21:1
    assert round(palette_validator.contrast("#000000", "#ffffff")) == 21


# ── svg_chart_kit primitives ─────────────────────────────────────────────────
def test_linear_scale() -> None:
    s = kit.LinearScale(100.0, 300.0, 10.0)
    assert s.x(0) == 100.0
    assert s.x(10) == 300.0
    assert s.x(5) == 200.0


def test_linear_scale_zero_max_safe() -> None:
    s = kit.LinearScale(100.0, 300.0, 0.0)
    assert s.x(5) == 100.0  # no divide-by-zero


def test_nice_ticks_from_zero() -> None:
    ticks = kit.nice_ticks_from_zero(13.2, 6)
    assert ticks[0] == 0.0
    assert ticks[-1] >= 13.2


def test_fmt_signed_uses_minus_glyph() -> None:
    assert kit.fmt_signed(5.2) == "+5.2"
    assert kit.fmt_signed(-39.27).startswith("−")  # U+2212, not hyphen
    assert "-" not in kit.fmt_signed(-39.27)  # ascii hyphen absent


def test_rrect_right_is_path_when_wide() -> None:
    out = kit.rrect_right(0, 0, 100, 18, "#2a78d6", r=4.0)
    assert out.startswith("<path")
    assert 'fill="#2a78d6"' in out


def test_rrect_right_falls_back_to_rect_when_tiny() -> None:
    out = kit.rrect_right(0, 0, 2, 18, "#2a78d6", r=4.0)
    assert out.startswith("<rect")


def test_draw_stack_returns_end_pixel_and_skips_zero() -> None:
    parts: list[str] = []
    scale = kit.LinearScale(0.0, 100.0, 10.0)
    end = kit.draw_stack(parts, 0, 18, [(5.0, "#2a78d6"), (0.0, "#eb6834"), (5.0, "#4a3aa7")], scale)
    assert abs(end - 100.0) < 1e-6           # 5 + 5 = 10 -> full width
    # only two non-zero segments drawn
    assert len(parts) == 2


def test_wrap_text() -> None:
    lines = kit.wrap_text("a b c d e f", chars=3)
    assert all(len(ln) <= 4 for ln in lines)


def test_svg_open_close_roundtrip(tmp_path: Path) -> None:
    parts = kit.svg_open(200, 100, kit.Theme(), provenance="unit test")
    parts.append(kit.text(10, 20, "hi", "title"))
    out = tmp_path / "t.svg"
    kit.svg_close(parts, out)
    txt = out.read_text()
    assert txt.startswith("<svg")
    assert txt.rstrip().endswith("</svg>")
    assert "<!-- unit test -->" in txt
    assert re.search(r'class="title">hi</text>', txt)


def test_esc_escapes_markup() -> None:
    assert kit.esc("<b>&") == "&lt;b&gt;&amp;"
