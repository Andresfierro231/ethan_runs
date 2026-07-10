#!/usr/bin/env python3
"""svg_timeseries_chart.py — line / trend / CLT SVG charts (stdlib only).

2-D time-series charts built on the shared `svg_chart_kit` theme and primitives:

  - `line_chart`        full value-vs-time, one line per series (or an ensemble
                        + mean overlay when there are many series).
  - `trend_window_chart` a windowed scatter/line with a fitted linear trendline
                        per series; the equation and R² go in the legend.
  - `sem_convergence_chart` log-log standard-error-of-the-mean vs averaging time
                        with a 1/√t (CLT) reference line.

Colours use the dataviz categorical order; validate any new palette with
`palette_validator.py`. Text wears ink tokens; the coloured mark carries identity.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from svg_chart_kit import Theme, esc, line, svg_close, svg_open, text, wrap_text

# Validated categorical order (dataviz reference palette).
LINE_PALETTE = ["#2a78d6", "#1baf7a", "#eda100", "#008300",
                "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]
ENSEMBLE_COLOR = "#9ec5f4"   # light blue for many thin lines
MEAN_COLOR = "#184f95"       # dark blue for the overlaid mean
MAX_NAMED_LINES = 8


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def nice_ticks(lo: float, hi: float, target: int = 6) -> list[float]:
    if lo == hi:
        pad = abs(lo) * 0.1 or 1.0
        lo, hi = lo - pad, hi + pad
    raw = (hi - lo) / max(target - 1, 1)
    mag = 10 ** math.floor(math.log10(abs(raw))) if raw > 0 else 1.0
    r = raw / mag
    step = 10 * mag if r > 5 else (5 * mag if r > 2 else (2 * mag if r > 1 else mag))
    start = math.floor(lo / step) * step
    ticks, v = [], start
    for _ in range(200):
        if v > hi + step * 0.5:
            break
        ticks.append(round(v, 10))
        v += step
    return ticks


def fmt_axis(v: float, span: float) -> str:
    """Scientific-ish single-value formatter (used for log axes)."""
    if span == 0:
        span = abs(v) or 1.0
    if abs(v) >= 1000 or (v != 0 and abs(v) < 0.001):
        return f"{v:.2e}"
    if span >= 100:
        return f"{v:.0f}"
    if span >= 5:
        return f"{v:.1f}"
    if span >= 0.5:
        return f"{v:.2f}"
    return f"{v:.4g}"


def lin_tick_labels(ticks: list[float]) -> list[str]:
    """Adaptive fixed-decimal labels for a linear axis.

    Decimals are chosen from the tick STEP so adjacent ticks are distinguishable
    even when the values sit on a large offset (e.g. mdot ≈ −0.0132 with a 5e-5
    step, or time = 7700 with a 100 s step). Falls back to scientific only when
    the magnitude is extreme.
    """
    uniq = sorted(set(ticks))
    if len(uniq) < 2:
        v = uniq[0] if uniq else 0.0
        return [f"{v:.3g}" for _ in ticks]
    step = min(b - a for a, b in zip(uniq, uniq[1:]) if b > a)
    big = max(abs(t) for t in ticks)
    if step <= 0 or big >= 1e6 or step < 1e-6:
        return [f"{v:.2e}" for v in ticks]
    decimals = max(0, math.ceil(-math.log10(step)))
    return [f"{v:.{decimals}f}" for v in ticks]


def _sig(v: float) -> str:
    return f"{v:.3g}"


class Frame:
    """A 2-D plot frame with linear or log scales."""

    def __init__(self, x0, x1, y0, y1, xmin, xmax, ymin, ymax, xlog=False, ylog=False):
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        self.xlog, self.ylog = xlog, ylog

    def px(self, v):
        a, b = self.xmin, self.xmax
        if self.xlog:
            v, a, b = math.log10(v), math.log10(a), math.log10(b)
        return self.x0 + (v - a) / (b - a) * (self.x1 - self.x0) if b != a else self.x0

    def py(self, v):
        a, b = self.ymin, self.ymax
        if self.ylog:
            v, a, b = math.log10(max(v, 1e-300)), math.log10(a), math.log10(b)
        return self.y1 - (v - a) / (b - a) * (self.y1 - self.y0) if b != a else self.y1


def _polyline(pts: list[tuple[float, float]], stroke: str, width: float,
              dash: str | None = None, opacity: float = 1.0) -> str:
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    op = f' stroke-opacity="{opacity}"' if opacity != 1.0 else ""
    return (f'<polyline points="{d}" fill="none" stroke="{stroke}" '
            f'stroke-width="{width}"{da}{op}/>')


def _range(vals: list[float], pad_frac: float = 0.06) -> tuple[float, float]:
    lo, hi = min(vals), max(vals)
    if lo == hi:
        pad = abs(lo) * 0.1 or 1.0
        return lo - pad, hi + pad
    pad = (hi - lo) * pad_frac
    return lo - pad, hi + pad


def _axes(parts, theme, fr, xlabel, ylabel, xticks, yticks):
    xspan = fr.xmax - fr.xmin
    yspan = fr.ymax - fr.ymin
    xlab = [fmt_axis(t, xspan) for t in xticks] if fr.xlog else lin_tick_labels(xticks)
    ylab = [fmt_axis(t, yspan) for t in yticks] if fr.ylog else lin_tick_labels(yticks)
    for xt, lab in zip(xticks, xlab):
        if xt < fr.xmin or xt > fr.xmax:
            continue
        xx = fr.px(xt)
        parts.append(line(xx, fr.y0, xx, fr.y1, theme.grid, 1.0))
        parts.append(text(xx, fr.y1 + 15, lab, "tick", anchor="middle"))
    for yt, lab in zip(yticks, ylab):
        if yt < fr.ymin or yt > fr.ymax:
            continue
        yy = fr.py(yt)
        parts.append(line(fr.x0, yy, fr.x1, yy, theme.grid, 1.0))
        parts.append(text(fr.x0 - 8, yy + 3, lab, "tick", anchor="end"))
    parts.append(line(fr.x0, fr.y0, fr.x0, fr.y1, theme.baseline, 1.0))
    parts.append(line(fr.x0, fr.y1, fr.x1, fr.y1, theme.baseline, 1.0))
    parts.append(text((fr.x0 + fr.x1) / 2, fr.y1 + 34, xlabel, "axislbl", anchor="middle"))
    cy = (fr.y0 + fr.y1) / 2
    parts.append(f'<text x="16" y="{cy:.1f}" text-anchor="middle" class="axislbl" '
                 f'transform="rotate(-90 16 {cy:.1f})">{esc(ylabel)}</text>')


def _legend_block(parts, items: list[tuple[str, str]], x: float, y: float,
                  line_h: float = 15.0) -> None:
    """Vertical legend: [(colour, text)]; text may be multi-field."""
    for i, (color, label) in enumerate(items):
        yy = y + i * line_h
        parts.append(f'<rect x="{x:.1f}" y="{yy - 9:.1f}" width="12" height="12" '
                     f'fill="{color}" rx="2"/>')
        parts.append(text(x + 18, yy + 1, label, "legend"))


# ---------------------------------------------------------------------------
# 1. full time series
# ---------------------------------------------------------------------------
def line_chart(path: Path, title: str, subtitle: str, series: Sequence,
               xlabel: str, ylabel: str, note: str, provenance: str,
               width: int = 1000, plot_h: int = 400) -> None:
    theme = Theme()
    all_t = [v for s in series for v in s.t]
    all_y = [v for s in series for v in s.y]
    if not all_t:
        return
    ensemble = len(series) > MAX_NAMED_LINES
    legend_rows = 2 if ensemble else len(series)
    note_lines = len(wrap_text(note, 150))
    L, R, T = 82, 30, 74
    B = 46 + legend_rows * 15 + note_lines * 12 + 18
    height = T + plot_h + B
    xmin, xmax = min(all_t), max(all_t)
    ymin, ymax = _range(all_y)
    fr = Frame(L, width - R, T, T + plot_h, xmin, xmax, ymin, ymax)
    parts = svg_open(width, height, theme, provenance)
    parts.append(text(L, 30, title, "title"))
    parts.append(text(L, 50, subtitle, "subtitle"))
    _axes(parts, theme, fr, xlabel, ylabel, nice_ticks(xmin, xmax), nice_ticks(ymin, ymax))

    legend: list[tuple[str, str]] = []
    if ensemble:
        for s in series:
            pts = [(fr.px(t), fr.py(y)) for t, y in zip(s.t, s.y)]
            parts.append(_polyline(pts, ENSEMBLE_COLOR, 0.8, opacity=0.5))
        n = min(len(s.y) for s in series)
        if n and all(len(s.y) >= n for s in series):
            base = series[0].t[:n]
            mean_y = [sum(s.y[i] for s in series) / len(series) for i in range(n)]
            pts = [(fr.px(t), fr.py(y)) for t, y in zip(base, mean_y)]
            parts.append(_polyline(pts, MEAN_COLOR, 2.0))
        legend = [(ENSEMBLE_COLOR, f"{len(series)} individual series"),
                  (MEAN_COLOR, "ensemble mean")]
    else:
        for i, s in enumerate(series):
            color = LINE_PALETTE[i % len(LINE_PALETTE)]
            pts = [(fr.px(t), fr.py(y)) for t, y in zip(s.t, s.y)]
            parts.append(_polyline(pts, color, 1.6))
            legend.append((color, s.name))

    legend_y = fr.y1 + 44
    _legend_block(parts, legend, L, legend_y)
    note_y = legend_y + legend_rows * 15 + 8
    for j, ln in enumerate(wrap_text(note, 150)):
        parts.append(text(L, note_y + j * 12, ln, "note"))
    svg_close(parts, path)


# ---------------------------------------------------------------------------
# 2. windowed trend
# ---------------------------------------------------------------------------
def trend_window_chart(path: Path, title: str, subtitle: str, entries: list[dict],
                       xlabel: str, ylabel: str, unit: str, note: str, provenance: str,
                       width: int = 1000, plot_h: int = 380) -> None:
    """entries: [{name, t, y, slope, intercept, r2, rmse, mean, sem}]."""
    theme = Theme()
    all_t = [v for e in entries for v in e["t"]]
    all_y = [v for e in entries for v in e["y"]]
    if not all_t:
        return
    note_lines = len(wrap_text(note, 155))
    L, R, T = 88, 30, 74
    B = 44 + len(entries) * 15 + note_lines * 12 + 16
    height = T + plot_h + B
    xmin, xmax = min(all_t), max(all_t)
    ymin, ymax = _range(all_y, 0.10)
    fr = Frame(L, width - R, T, T + plot_h, xmin, xmax, ymin, ymax)
    parts = svg_open(width, height, theme, provenance)
    parts.append(text(L, 30, title, "title"))
    parts.append(text(L, 50, subtitle, "subtitle"))
    _axes(parts, theme, fr, xlabel, ylabel, nice_ticks(xmin, xmax), nice_ticks(ymin, ymax))

    legend: list[tuple[str, str]] = []
    for i, e in enumerate(entries):
        color = LINE_PALETTE[i % len(LINE_PALETTE)]
        pts = [(fr.px(t), fr.py(y)) for t, y in zip(e["t"], e["y"])]
        parts.append(_polyline(pts, color, 1.3, opacity=0.55))
        x0, x1 = e["t"][0], e["t"][-1]
        ya, yb = e["slope"] * x0 + e["intercept"], e["slope"] * x1 + e["intercept"]
        parts.append(_polyline([(fr.px(x0), fr.py(ya)), (fr.px(x1), fr.py(yb))],
                               color, 2.6, dash="7,4"))
        sign = "+" if e["intercept"] >= 0 else "−"
        eq = f'{e["name"]}:  y = {_sig(e["slope"])}·t {sign} {_sig(abs(e["intercept"]))}   R² = {e["r2"]:.3f}'
        legend.append((color, eq))

    legend_y = fr.y1 + 42
    _legend_block(parts, legend, L, legend_y, line_h=15)
    note_y = legend_y + len(entries) * 15 + 8
    for j, ln in enumerate(wrap_text(note, 155)):
        parts.append(text(L, note_y + j * 12, ln, "note"))
    svg_close(parts, path)


# ---------------------------------------------------------------------------
# 3. SEM convergence (CLT, log-log)
# ---------------------------------------------------------------------------
def sem_convergence_chart(path: Path, title: str, subtitle: str, points: list[dict],
                          ylabel: str, note: str, provenance: str,
                          width: int = 900, height: int = 560) -> None:
    """points: [{avg_seconds, sem_naive, sem_reference}] (positive values)."""
    theme = Theme()
    L, R, T, B = 84, 34, 74, 108
    xs = [p["avg_seconds"] for p in points if p["avg_seconds"] > 0]
    ys = [p["sem_naive"] for p in points if p["sem_naive"] > 0] + \
         [p["sem_reference"] for p in points if p["sem_reference"] > 0]
    if not xs or not ys:
        return
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys) * 0.7, max(ys) * 1.4
    fr = Frame(L, width - R, T, height - B, xmin, xmax, ymin, ymax, xlog=True, ylog=True)
    parts = svg_open(width, height, theme, provenance)
    parts.append(text(L, 30, title, "title"))
    parts.append(text(L, 50, subtitle, "subtitle"))
    _axes(parts, theme, fr, "averaging duration (s, log)", ylabel + " (log)",
          _decades(xmin, xmax), _decades(ymin, ymax))

    ref = [(fr.px(p["avg_seconds"]), fr.py(p["sem_reference"]))
           for p in points if p["avg_seconds"] > 0 and p["sem_reference"] > 0]
    parts.append(_polyline(ref, "#898781", 2.0, dash="6,4"))
    obs = [(fr.px(p["avg_seconds"]), fr.py(p["sem_naive"]))
           for p in points if p["avg_seconds"] > 0 and p["sem_naive"] > 0]
    parts.append(_polyline(obs, LINE_PALETTE[0], 2.2))
    for x, y in obs:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{LINE_PALETTE[0]}"/>')

    _legend_block(parts, [(LINE_PALETTE[0], "observed SEM = σ(window)/√N"),
                          ("#898781", "ideal CLT reference ∝ 1/√t")],
                  L, height - B + 46)
    for j, ln in enumerate(wrap_text(note, 140)):
        parts.append(text(L, height - 16 + j * 12, ln, "note"))
    svg_close(parts, path)


def _decades(lo: float, hi: float) -> list[float]:
    """1-2-5 ticks spanning [lo, hi] for a log axis."""
    if lo <= 0:
        lo = hi / 1000 if hi > 0 else 1e-6
    out: list[float] = []
    e = math.floor(math.log10(lo))
    while 10 ** e <= hi * 1.5:
        for m in (1, 2, 5):
            v = m * 10 ** e
            if lo * 0.5 <= v <= hi * 1.5:
                out.append(v)
        e += 1
    return out or [lo, hi]
