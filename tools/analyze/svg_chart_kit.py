#!/usr/bin/env python3
"""svg_chart_kit.py — small dependency-free toolkit for horizontal bar figures.

A reusable set of SVG primitives for building slide/thesis-quality horizontal bar
charts with the standard library only (no matplotlib), so figures can be rebuilt
in a minimal HPC shell. It encodes the dataviz mark spec used across this repo's
figure scripts:

  - one off-white chart surface, ink/grid/baseline tokens (light mode)
  - thin bars with a 2 px surface gap between stacked segments
  - a 4 px rounded outer *data-end* (left square, right rounded)
  - a recessive hairline grid, one axis line, tabular-num ticks
  - section-header rows for grouping (never a second label column)

Import the pieces you need; the caller owns the figure-specific data mapping.
`Theme` holds the colour tokens (swap for a brand); `LinearScale` maps values to
pixels; `draw_stack` renders a stacked bar and returns its end pixel so the caller
can place a direct value label.

This module carries NO project data. It is pure presentation. Every scientific
choice (which column maps to which bar, units, sign convention) lives in the
calling script and its data-disclosure output.
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

FONT = 'system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif'


@dataclass(frozen=True)
class Theme:
    """Chart chrome & ink tokens (dataviz reference palette, light mode)."""
    surface: str = "#fcfcfb"
    ink: str = "#0b0b0b"
    ink2: str = "#52514e"
    muted: str = "#898781"
    grid: str = "#e1e0d9"
    baseline: str = "#c3c2b7"
    good_ink: str = "#006300"   # for signed/positive-delta text
    font: str = FONT


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


# ── canvas ──────────────────────────────────────────────────────────────────────
def svg_open(width: int, height: int, theme: Theme, provenance: str = "") -> list[str]:
    """Return the opening SVG lines with the standard class stylesheet.

    `provenance` (optional) is written as an XML comment so the figure is
    self-documenting when opened as text.
    """
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
    ]
    if provenance:
        parts.append(f"<!-- {esc(provenance)} -->")
    parts += [
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{theme.surface}"/>',
        "<style>",
        f"text{{font-family:{theme.font};fill:{theme.ink}}}",
        f".title{{font-size:19px;font-weight:700;fill:{theme.ink}}}",
        f".subtitle{{font-size:11.5px;fill:{theme.ink2}}}",
        f".section{{font-size:12px;font-weight:700;fill:{theme.ink2}}}",
        f".spanlbl{{font-size:11px;fill:{theme.ink}}}",
        f".spanlbl-r{{font-size:11px;fill:{theme.muted};font-style:italic}}",
        f".axislbl{{font-size:11px;fill:{theme.ink2}}}",
        f".tick{{font-size:10px;fill:{theme.muted};font-variant-numeric:tabular-nums}}",
        f".val{{font-size:10px;fill:{theme.ink};font-weight:600;font-variant-numeric:tabular-nums}}",
        f".valg{{font-size:10px;fill:{theme.good_ink};font-weight:600;font-variant-numeric:tabular-nums}}",
        f".legend{{font-size:11px;fill:{theme.ink}}}",
        f".note{{font-size:10px;fill:{theme.muted}}}",
        "</style>",
    ]
    return parts


def svg_close(parts: list[str], path: Path) -> None:
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))


# ── primitives ────────────────────────────────────────────────────────────────
def rect(x: float, y: float, w: float, h: float, fill: str, opacity: float = 1.0) -> str:
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0.5):.1f}" '
            f'height="{h:.1f}" fill="{fill}"{op}/>')


def rrect_right(x: float, y: float, w: float, h: float, fill: str, r: float = 4.0) -> str:
    """Rect with only the right (data-end) corners rounded; left stays square."""
    w = max(w, 0.5)
    r = min(r, h / 2, w)
    if w <= r + 0.5:
        return rect(x, y, w, h, fill)
    return (
        f'<path d="M{x:.1f},{y:.1f} H{x + w - r:.1f} '
        f'Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} '
        f'V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} '
        f'H{x:.1f} Z" fill="{fill}"/>'
    )


def line(x1: float, y1: float, x2: float, y2: float, stroke: str,
         width: float = 1.0, dash: str | None = None) -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{width}"{d}/>')


def text(x: float, y: float, s: str, cls: str, anchor: str = "start") -> str:
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x:.1f}" y="{y:.1f}"{a} class="{cls}">{esc(s)}</text>'


# ── scale ─────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class LinearScale:
    """Map a value in [0, v_max] to a pixel in [x0_px, x1_px]."""
    x0_px: float
    x1_px: float
    v_max: float

    def x(self, value: float) -> float:
        if self.v_max <= 0:
            return self.x0_px
        return self.x0_px + value / self.v_max * (self.x1_px - self.x0_px)


def nice_ticks_from_zero(hi: float, target: int = 6) -> list[float]:
    """Ticks 0 → a nice number >= hi (for magnitude axes anchored at zero)."""
    if hi <= 0:
        return [0.0, 1.0]
    raw = hi / max(target - 1, 1)
    mag = 10 ** math.floor(math.log10(abs(raw)))
    r = raw / mag
    nice = 10 * mag if r > 5 else (5 * mag if r > 2 else (2 * mag if r > 1 else mag))
    ticks: list[float] = []
    v = 0.0
    for _ in range(80):
        ticks.append(round(v, 10))
        if v >= hi:
            break
        v += nice
    return ticks


def fmt_num(v: float) -> str:
    if abs(v) >= 100:
        return f"{v:.0f}"
    if abs(v) >= 1:
        return f"{v:.1f}"
    return f"{v:.2f}"


def fmt_signed(v: float) -> str:
    """Signed value with a proper minus glyph (U+2212)."""
    s = fmt_num(abs(v))
    return f"+{s}" if v >= 0 else f"−{s}"


def wrap_text(s: str, chars: int = 150) -> list[str]:
    words = s.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        if len(" ".join(cur + [w])) > chars and cur:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


# ── composed helpers ────────────────────────────────────────────────────────────
def draw_axis(parts: list[str], theme: Theme, scale: LinearScale, ticks: Sequence[float],
              top: float, bottom: float) -> None:
    """Vertical gridlines with tick labels above the plot, plus L/bottom axis lines."""
    for t in ticks:
        xx = scale.x(t)
        parts.append(line(xx, top, xx, bottom, theme.grid, 1.0))
        parts.append(text(xx, top - 8, fmt_num(t), "tick", anchor="middle"))
    parts.append(line(scale.x0_px, top, scale.x0_px, bottom, theme.baseline, 1.0))
    parts.append(line(scale.x0_px, bottom, scale.x1_px, bottom, theme.baseline, 1.0))


def draw_section_header(parts: list[str], theme: Theme, label: str, x_left: float,
                        y: float, x_right: float, height: float) -> None:
    parts.append(text(x_left, y + 17, label, "section"))
    parts.append(line(x_left, y + height - 4, x_right, y + height - 4, theme.grid, 1.0))


def draw_stack(parts: list[str], y: float, bar_h: float,
               segments: Sequence[tuple[float, str]], scale: LinearScale,
               gap: float = 2.0, r: float = 4.0) -> float:
    """Draw a stacked horizontal bar from value 0; return the true end pixel.

    `segments` is [(value, colour), ...]; zero/negative segments are skipped. A
    2 px surface gap separates interior segments; only the outer end is rounded.
    """
    segs = [(v, c) for v, c in segments if v > 0]
    cursor = 0.0
    for idx, (val, color) in enumerate(segs):
        xa = scale.x(cursor)
        xb = scale.x(cursor + val)
        is_last = idx == len(segs) - 1
        right = xb if is_last else xb - gap
        if is_last:
            parts.append(rrect_right(xa, y, right - xa, bar_h, color, r=r))
        else:
            parts.append(rect(xa, y, right - xa, bar_h, color))
        cursor += val
    return scale.x(cursor)


def draw_legend(parts: list[str], items: Sequence[tuple[str, str]], x: float, y: float,
                char_px: float = 6.4) -> None:
    """Inline legend: [(colour, label), ...] laid out left-to-right on one row."""
    lx = x
    for color, label in items:
        parts.append(f'<rect x="{lx:.1f}" y="{y - 10:.1f}" width="13" height="13" '
                     f'fill="{color}" rx="2"/>')
        parts.append(text(lx + 19, y, label, "legend"))
        lx += 24 + len(label) * char_px


def draw_note(parts: list[str], theme: Theme, s: str, x: float, y: float,
              chars: int = 150, line_h: float = 13.0) -> float:
    for idx, ln in enumerate(wrap_text(s, chars)):
        parts.append(text(x, y + idx * line_h, ln, "note"))
    return y + len(wrap_text(s, chars)) * line_h
