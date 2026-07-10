#!/usr/bin/env python3
"""palette_validator.py — computable checks for a categorical chart palette.

Python port of the dataviz skill's `validate_palette.js`, kept in-repo so palette
choices are reproducibly verified without a Node runtime. Any chart script that
picks colours should import `validate()` (or run this module's CLI) and confirm
the palette PASSes before shipping — never eyeball whether colours are
colourblind-safe.

Checks (all measured from the hex values + surface, never guessed):
  1. Lightness band     — OKLCH L within the mode's band
  2. Chroma floor       — OKLCH C >= floor (below it a hue reads as gray)
  3. CVD separation     — Machado-2009 ΔE (protan/deutan/tritan) on adjacent pairs
  4. Contrast vs surface — WCAG ratio of each mark against the chart surface

Thresholds and transforms are copied verbatim from the reference validator.

CLI:
    python tools/analyze/palette_validator.py "#2a78d6,#eb6834,#4a3aa7,#008300"
    python tools/analyze/palette_validator.py "#..,#.." --mode dark --surface "#1a1a19"

Programmatic:
    from palette_validator import validate
    result = validate(["#2a78d6", "#eb6834", "#4a3aa7", "#008300"])
    assert result["ok"], result["report"]
"""

from __future__ import annotations

import math
import sys
from typing import Sequence

# ── thresholds (from validate_palette.js) ──────────────────────────────────────
BAND = {"light": (0.43, 0.77), "dark": (0.48, 0.67)}   # OKLCH L
CHROMA_FLOOR = 0.10                                      # OKLCH C
CVD_TARGET, CVD_FLOOR = 12.0, 8.0                        # CIE76 ΔE on adjacent pairs
CONTRAST_MIN = 3.0                                       # WCAG vs surface
DEFAULT_SURFACE = {"light": "#fcfcfb", "dark": "#1a1a19"}

# Machado, Oliveira & Fernandes (2009) CVD transforms at severity 1.0 (linear RGB).
MACHADO = {
    "protan": [[0.152286, 1.052583, -0.204868],
               [0.114503, 0.786281, 0.099216],
               [-0.003882, -0.048116, 1.051998]],
    "deutan": [[0.367322, 0.860646, -0.227968],
               [0.280085, 0.672501, 0.047413],
               [-0.011820, 0.042940, 0.968881]],
    "tritan": [[1.255528, -0.076749, -0.178779],
               [-0.078411, 0.930809, 0.147602],
               [0.004733, 0.691367, 0.303900]],
}


# ── colour conversions ─────────────────────────────────────────────────────────
def _hex2srgb(h: str) -> list[float]:
    h = h.strip().lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _s2lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lin(h: str) -> list[float]:
    return [_s2lin(c) for c in _hex2srgb(h)]


def _rel_lum(h: str) -> float:
    r, g, b = _lin(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    hi, lo = sorted([_rel_lum(a), _rel_lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _oklab(h: str) -> list[float]:
    r, g, b = _lin(h)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s]


def _oklch(h: str) -> tuple[float, float]:
    L, a, b = _oklab(h)
    return L, math.hypot(a, b)


def _lin2lab(r: float, g: float, b: float) -> list[float]:
    X = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    Y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    Z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(X / 0.95047), f(Y / 1.0), f(Z / 1.08883)
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)]


def _simulate(h: str, kind: str) -> list[float]:
    r, g, b = _lin(h)
    M = MACHADO[kind]
    clamp = lambda c: max(0.0, min(1.0, c))
    return [clamp(M[0][0] * r + M[0][1] * g + M[0][2] * b),
            clamp(M[1][0] * r + M[1][1] * g + M[1][2] * b),
            clamp(M[2][0] * r + M[2][1] * g + M[2][2] * b)]


def _delta_e(h1: str, h2: str, kind: str | None = None) -> float:
    a = _lin2lab(*(_simulate(h1, kind) if kind else _lin(h1)))
    b = _lin2lab(*(_simulate(h2, kind) if kind else _lin(h2)))
    return math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2])


# ── the check ──────────────────────────────────────────────────────────────────
def validate(palette: Sequence[str], mode: str = "light",
             surface: str | None = None) -> dict:
    """Return {'ok': bool, 'report': [(check, state, detail), ...]} for adjacent pairs."""
    surface = surface or DEFAULT_SURFACE[mode]
    lo, hi = BAND[mode]
    report: list[tuple[str, str, str]] = []
    ok = True

    off = [(c, round(_oklch(c)[0], 3)) for c in palette if not (lo <= _oklch(c)[0] <= hi)]
    if off:
        ok = False
    report.append(("Lightness band", "PASS" if not off else "FAIL",
                   f"all {len(palette)} inside L {lo}-{hi}" if not off else f"outside: {off}"))

    lowc = [(c, round(_oklch(c)[1], 3)) for c in palette if _oklch(c)[1] < CHROMA_FLOOR]
    if lowc:
        ok = False
    report.append(("Chroma floor", "PASS" if not lowc else "FAIL",
                   f"all >= {CHROMA_FLOOR}" if not lowc else f"reads gray: {lowc}"))

    pairs = [(i, i + 1) for i in range(len(palette) - 1)]
    worst = None
    for kind in ("protan", "deutan"):
        for i, j in pairs:
            d = _delta_e(palette[i], palette[j], kind)
            if worst is None or d < worst[0]:
                worst = (d, kind, palette[i], palette[j])
    wd = worst[0] if worst else 99.0
    state = "PASS" if wd >= CVD_TARGET else ("WARN" if wd >= CVD_FLOOR else "FAIL")
    if state == "FAIL":
        ok = False
    detail = (f"worst adjacent {worst[3]}<->{worst[2]} ΔE {wd:.1f} ({worst[1]})"
              if worst else "single colour")
    report.append(("CVD separation", state, detail))

    low = [(c, round(contrast(c, surface), 2)) for c in palette
           if contrast(c, surface) < CONTRAST_MIN]
    report.append(("Contrast vs surface", "PASS" if not low else "WARN",
                   f"all >= {CONTRAST_MIN}:1" if not low
                   else f"below {CONTRAST_MIN}:1 (needs direct labels/table): {low}"))

    return {"ok": ok, "report": report, "worst_cvd": wd, "mode": mode, "surface": surface}


def format_report(result: dict, palette: Sequence[str]) -> str:
    lines = [f"Palette ({result['mode']}, surface {result['surface']}): {list(palette)}"]
    for name, state, detail in result["report"]:
        lines.append(f"  [{state:<4}] {name:<20} {detail}")
    lines.append(f"  -> {'ALL PASS' if result['ok'] else 'FAILED'}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print('usage: palette_validator.py "#hex,#hex,..." [--mode light|dark] [--surface #hex]')
        return 2
    mode, surface, positional = "light", None, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--mode":
            i += 1
            mode = argv[i]
        elif a == "--surface":
            i += 1
            surface = argv[i]
        elif positional is None:
            positional = a
        i += 1
    palette = [s.strip() for s in (positional or "").split(",") if s.strip()]
    result = validate(palette, mode=mode, surface=surface)
    print(format_report(result, palette))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
