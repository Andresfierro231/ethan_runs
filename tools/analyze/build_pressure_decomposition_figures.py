#!/usr/bin/env python3
"""build_pressure_decomposition_figures.py — pressure-ledger figures (AGENT-234).

Reads the July 8 pressure term ledger and produces two clean SVG figures plus a
full data-disclosure sidecar. The reusable presentation primitives live in
`svg_chart_kit.py`; the palette is verified by `palette_validator.py` at build
time. This script owns only the pressure-specific data mapping and disclosure.

Figures
-------
1. mechanical_loss_composition_by_span.svg
   Horizontal STACKED bars: de-buoyed friction | development/reset | minor-loss
   upper bound. One row per span; Salt 2/3/4 grouped under section headers. The
   total bar length is the complete estimated irreversible loss.

2. buoyancy_drive_vs_resistance_by_span.svg
   Paired bars per span: buoyancy driving-term magnitude (green) vs total
   mechanical resistance (blue), each on its own baseline (nothing overlaps).
   Buoyancy labels keep their sign, so the downcomer's large negative
   (downward-driving) term is unambiguous.

Data disclosure
---------------
Every value that appears in either figure is written verbatim to
`figure_data.csv`, and `DATA_DISCLOSURE.md` states exactly which ledger column
maps to which visual element, the units, the sign convention, and what is
excluded. Nothing plotted is hidden or silently transformed.

HOW THIS WAS MADE (reproducible method)
---------------------------------------
1. Read the pressure term ledger CSV (read-only). Keep Salt 2/3/4 Jin mainline
   rows only (Salt 1 is weakly converged and excluded).
2. Map ledger columns to plot quantities (see DATA_DISCLOSURE / summary.json):
     distributed_friction_pa   -> friction segment
     development_loss_pa        -> development/reset segment
     minor_loss_pa              -> minor-loss upper-bound segment
     buoyancy_contribution_pa   -> buoyancy driving term (signed)
3. Choose a categorical palette and VALIDATE it with palette_validator.validate()
   (OKLCH lightness band, chroma floor, Machado-2009 CVD ΔE, WCAG contrast). The
   build asserts the palette PASSes; the result is recorded in summary.json.
4. Lay out with svg_chart_kit: section-header rows for case grouping (so case
   names never collide with span labels), a recessive hairline grid, 2 px surface
   gaps between stacked segments, 4 px rounded outer data-ends, one legend, and a
   direct value label on every bar.
5. Emit figures + figure_data.csv + DATA_DISCLOSURE.md + README.md + summary.json.
6. Render to PNG and eyeball for collisions/overflow before shipping (dataviz
   "render it and look at it" step; command in README).

Usage
-----
    python tools/analyze/build_pressure_decomposition_figures.py
    python tools/analyze/build_pressure_decomposition_figures.py \\
        --output-dir <dir> --ledger <pressure_term_ledger.csv>

MODELING ASSUMPTIONS
--------------------
Buoyancy term: buoyancy_contribution_pa = gh_drho_dxi_pa_m x L_m (station-order
  product; sign follows the momentum-budget identity). For the downcomer
  (upper_leg) it is large and NEGATIVE: the density-gradient force acts opposite
  to the reference positive flow direction. It still DRIVES natural circulation.
  Figure 2 plots |buoyancy| and keeps the sign in the label; a negative bar is
  not an energy loss.
Development/reset: max(Shah total dp - F1 total dp, 0) for entry spans
  (flow_reset_flag=True). Non-entry spans (test_section_span, left_upper_leg)
  inherit developed flow -> 0.
Minor loss: upper bound (local dynamic-head normalization overestimates); not an
  additive correction.
De-buoyed friction: distributed_friction_pa, always positive; viscous + turbulent
  stress over the span with the buoyancy source subtracted.
Recirculation spans (left_lower_leg, left_upper_leg): single-stream friction is
  ambiguous (15-33% backflow); marked with `*`, diagnostic only.
Mesh/GCI: all rows coarse_no_gci; no uncertainty bounds; diagnostic quality.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Sequence

import palette_validator
import svg_chart_kit as kit
from svg_chart_kit import (
    LinearScale,
    Theme,
    draw_axis,
    draw_legend,
    draw_note,
    draw_section_header,
    draw_stack,
    fmt_num,
    fmt_signed,
    nice_ticks_from_zero,
    rrect_right,
    svg_close,
    svg_open,
    text,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger"
    / "pressure_term_ledger.csv"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures"
)

TASK_ID = "AGENT-234"

# Palette — validated by palette_validator at build time (all checks PASS, light).
C_FRICTION = "#2a78d6"   # blue   — de-buoyed distributed friction
C_DEV = "#eb6834"        # orange — development / entry-length reset
C_MINOR = "#4a3aa7"      # violet — minor-loss upper bound
C_BUOYANCY = "#008300"   # green  — density-gradient buoyancy driving term
C_MECH = C_FRICTION      # mechanical total reuses friction blue in figure 2
PALETTE = [C_FRICTION, C_DEV, C_MINOR, C_BUOYANCY]

THEME = Theme()

SPAN_ORDER = [
    "lower_leg", "right_leg", "left_lower_leg",
    "test_section_span", "left_upper_leg", "upper_leg",
]
SPAN_LABELS = {
    "lower_leg": "Lower leg (heater)",
    "right_leg": "Right leg (downcomer)",
    "left_lower_leg": "Left lower (upcomer) *",
    "test_section_span": "Test section",
    "left_upper_leg": "Left upper (upcomer) *",
    "upper_leg": "Upper leg (downcomer)",
}
CASE_ORDER = ["salt_2", "salt_3", "salt_4"]
CASE_LABELS = {"salt_2": "Salt 2", "salt_3": "Salt 3", "salt_4": "Salt 4"}

# Exact ledger columns consumed → plotted quantity (drives DATA_DISCLOSURE.md).
COLUMN_MAP = {
    "distributed_friction_pa": "friction segment (fig 1 & 2)",
    "development_loss_pa": "development/reset segment (fig 1 & 2)",
    "minor_loss_pa": "minor-loss upper-bound segment (fig 1 & 2)",
    "buoyancy_contribution_pa": "buoyancy driving term, signed (fig 2)",
    "recirculation_flag": "asterisk / italic label on recirculation spans",
    "Re": "context only (not plotted; disclosed in figure_data.csv)",
}


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

def read_ledger(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Pressure ledger not found: {path}")
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _fnum(value: object, default: float = 0.0) -> float:
    t = str(value).strip()
    if not t or t.lower() in {"nan", "na", "none", ""}:
        return default
    return float(t)


def extract_rows(ledger: list[dict[str, str]]) -> list[dict]:
    """One dict per span/case, in canonical loop order (heater → downcomer)."""
    by_key: dict[tuple[str, str], dict] = {}
    for row in ledger:
        case, span = row["case_id"], row["span"]
        if case not in CASE_ORDER:
            continue
        by_key[(case, span)] = {
            "case": case,
            "span": span,
            "label": SPAN_LABELS.get(span, span),
            "friction": _fnum(row["distributed_friction_pa"]),
            "dev": _fnum(row["development_loss_pa"]),
            "minor": _fnum(row["minor_loss_pa"]),
            "buoyancy": _fnum(row["buoyancy_contribution_pa"]),
            "recirculation": row.get("recirculation_flag", "False").lower() == "true",
            "Re": _fnum(row.get("Re")),
        }
    return [by_key[(c, s)] for c in CASE_ORDER for s in SPAN_ORDER if (c, s) in by_key]


def mech_total(row: dict) -> float:
    return row["friction"] + row["dev"] + row["minor"]


# ---------------------------------------------------------------------------
# Figure 1 — Mechanical loss composition (stacked)
# ---------------------------------------------------------------------------

def build_mechanical_stacked(rows: list[dict], path: Path, provenance: str) -> None:
    WIDTH, MARGIN_L, LABEL_W, MARGIN_R = 1000, 22, 178, 84
    PLOT_X = MARGIN_L + LABEL_W
    PLOT_W = WIDTH - PLOT_X - MARGIN_R
    TOP, BAR_H, ROW_PITCH, SECTION_H = 78, 18, 27, 26

    ticks = nice_ticks_from_zero(max((mech_total(r) for r in rows), default=1.0), 6)
    scale = LinearScale(PLOT_X, PLOT_X + PLOT_W, max(ticks))
    plot_h = len(CASE_ORDER) * SECTION_H + len(rows) * ROW_PITCH
    plot_bottom = TOP + plot_h
    HEIGHT = int(plot_bottom + 20 + 60)

    parts = svg_open(WIDTH, HEIGHT, THEME, provenance)
    parts.append(text(MARGIN_L, 30, "Mechanical pressure loss by span", "title"))
    parts.append(text(MARGIN_L, 50,
                      "Salt 2 / 3 / 4 Jin mainline · irreversible losses only · coarse mesh, no GCI",
                      "subtitle"))
    draw_axis(parts, THEME, scale, ticks, TOP, plot_bottom)

    y = TOP
    for case in CASE_ORDER:
        case_rows = [r for r in rows if r["case"] == case]
        if not case_rows:
            continue
        draw_section_header(parts, THEME, CASE_LABELS[case], MARGIN_L, y,
                            PLOT_X + PLOT_W, SECTION_H)
        y += SECTION_H
        for row in case_rows:
            bar_y = y + (ROW_PITCH - BAR_H) / 2
            cls = "spanlbl-r" if row["recirculation"] else "spanlbl"
            parts.append(text(PLOT_X - 10, bar_y + BAR_H - 5, row["label"], cls, anchor="end"))
            end_x = draw_stack(parts, bar_y, BAR_H,
                               [(row["friction"], C_FRICTION), (row["dev"], C_DEV),
                                (row["minor"], C_MINOR)], scale)
            parts.append(text(end_x + 6, bar_y + BAR_H - 5,
                              f"{fmt_num(mech_total(row))} Pa", "val"))
            y += ROW_PITCH

    parts.append(text(PLOT_X + PLOT_W / 2, plot_bottom + 32,
                      "Pressure loss over span (Pa)", "axislbl", anchor="middle"))
    legend_y = plot_bottom + 42
    draw_legend(parts, [(C_FRICTION, "de-buoyed distributed friction"),
                        (C_DEV, "development / entry-length reset"),
                        (C_MINOR, "minor-loss upper bound")], MARGIN_L, legend_y)
    draw_note(parts, THEME,
              "* upcomer recirculation span — single-stream friction is a diagnostic only. "
              "Minor-loss bars are upper bounds. Source: 2026-07-08 pressure term ledger.",
              MARGIN_L, legend_y + 22)
    svg_close(parts, path)


# ---------------------------------------------------------------------------
# Figure 2 — Buoyancy drive vs mechanical resistance (paired bars)
# ---------------------------------------------------------------------------

def build_drive_vs_resistance(rows: list[dict], path: Path, provenance: str) -> None:
    WIDTH, MARGIN_L, LABEL_W, MARGIN_R = 1040, 22, 178, 92
    PLOT_X = MARGIN_L + LABEL_W
    PLOT_W = WIDTH - PLOT_X - MARGIN_R
    TOP, SUB_H, SUB_GAP, ROW_PITCH, SECTION_H = 82, 9, 3, 34, 26

    hi = max((max(abs(r["buoyancy"]), mech_total(r)) for r in rows), default=1.0)
    ticks = nice_ticks_from_zero(hi, 6)
    scale = LinearScale(PLOT_X, PLOT_X + PLOT_W, max(ticks))
    plot_h = len(CASE_ORDER) * SECTION_H + len(rows) * ROW_PITCH
    plot_bottom = TOP + plot_h
    HEIGHT = int(plot_bottom + 20 + 76)

    parts = svg_open(WIDTH, HEIGHT, THEME, provenance)
    parts.append(text(MARGIN_L, 30, "Buoyancy drive vs mechanical resistance by span", "title"))
    parts.append(text(MARGIN_L, 50,
                      "Bar length is magnitude in Pa; buoyancy labels keep their sign "
                      "(negative = drives flow downward in the downcomer).", "subtitle"))
    draw_axis(parts, THEME, scale, ticks, TOP, plot_bottom)

    y = TOP
    for case in CASE_ORDER:
        case_rows = [r for r in rows if r["case"] == case]
        if not case_rows:
            continue
        draw_section_header(parts, THEME, CASE_LABELS[case], MARGIN_L, y,
                            PLOT_X + PLOT_W, SECTION_H)
        y += SECTION_H
        for row in case_rows:
            pair_top = y + (ROW_PITCH - (2 * SUB_H + SUB_GAP)) / 2
            buoy, mech = row["buoyancy"], mech_total(row)
            cls = "spanlbl-r" if row["recirculation"] else "spanlbl"
            parts.append(text(PLOT_X - 10, pair_top + SUB_H + SUB_GAP / 2 + 3,
                              row["label"], cls, anchor="end"))
            # buoyancy bar (top)
            bx = scale.x(abs(buoy))
            parts.append(rrect_right(PLOT_X, pair_top, bx - PLOT_X, SUB_H, C_BUOYANCY, r=3.0))
            parts.append(text(bx + 6, pair_top + SUB_H - 1, fmt_signed(buoy), "valg"))
            # mechanical resistance bar (bottom)
            my = pair_top + SUB_H + SUB_GAP
            mx = scale.x(mech)
            parts.append(rrect_right(PLOT_X, my, mx - PLOT_X, SUB_H, C_MECH, r=3.0))
            parts.append(text(mx + 6, my + SUB_H - 1, fmt_num(mech), "val"))
            y += ROW_PITCH

    parts.append(text(PLOT_X + PLOT_W / 2, plot_bottom + 32,
                      "Magnitude over span (Pa)", "axislbl", anchor="middle"))
    legend_y = plot_bottom + 42
    draw_legend(parts, [(C_BUOYANCY, "buoyancy driving term (|gh·Δρ·L|, sign in label)"),
                        (C_MECH, "total mechanical resistance (friction + dev + minor)")],
                MARGIN_L, legend_y, char_px=6.6)
    draw_note(parts, THEME,
              "Buoyancy is reversible (a driving head), not a loss; a negative sign means it "
              "acts opposite to the reference flow direction and drives the downcomer. "
              "* upcomer recirculation span — single-stream interpretation is diagnostic only. "
              "Source: 2026-07-08 pressure term ledger.",
              MARGIN_L, legend_y + 22)
    svg_close(parts, path)


# ---------------------------------------------------------------------------
# Data disclosure
# ---------------------------------------------------------------------------

FIGURE_DATA_FIELDS = [
    "case_id", "case_label", "span_id", "span_label", "recirculation",
    "friction_pa", "dev_reset_pa", "minor_pa", "mechanical_total_pa",
    "buoyancy_signed_pa", "buoyancy_abs_pa", "Re",
]


def write_figure_data(output_dir: Path, rows: list[dict]) -> None:
    """Every value that appears in either figure, verbatim — full disclosure."""
    with (output_dir / "figure_data.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIGURE_DATA_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({
                "case_id": r["case"],
                "case_label": CASE_LABELS.get(r["case"], r["case"]),
                "span_id": r["span"],
                "span_label": r["label"],
                "recirculation": r["recirculation"],
                "friction_pa": f"{r['friction']:.4f}",
                "dev_reset_pa": f"{r['dev']:.4f}",
                "minor_pa": f"{r['minor']:.4f}",
                "mechanical_total_pa": f"{mech_total(r):.4f}",
                "buoyancy_signed_pa": f"{r['buoyancy']:.4f}",
                "buoyancy_abs_pa": f"{abs(r['buoyancy']):.4f}",
                "Re": f"{r['Re']:.2f}",
            })


def write_data_disclosure(output_dir: Path, rows: list[dict], ledger_path: Path,
                          palette_result: dict) -> None:
    src = str(ledger_path.relative_to(REPO_ROOT)) if ledger_path.is_relative_to(REPO_ROOT) else str(ledger_path)
    col_lines = "\n".join(f"| `{col}` | {role} |" for col, role in COLUMN_MAP.items())
    pal_lines = "\n".join(f"  [{s}] {n}: {d}" for n, s, d in palette_result["report"])
    txt = f"""# Data Disclosure — Pressure Decomposition Figures ({TASK_ID})

This file states exactly what data goes into each figure. Nothing plotted is
hidden or silently transformed. Every plotted value is also in
`figure_data.csv` (one row per span/case).

## Single source

- **Input:** `{src}`
- **Rows used:** {len(rows)} = {len(CASE_ORDER)} cases × {len(SPAN_ORDER)} spans
  (Salt 2/3/4 Jin mainline). Salt 1 Jin is excluded (weakly converged).
- **No new CFD extraction.** The ledger is read-only; figures are a presentation
  of already-audited values.

## Ledger column → visual element

| Ledger column | Role in the figures |
|---|---|
{col_lines}

Columns NOT used (deliberately excluded from the figures): `gross_static_dp_pa`,
`residual_pa`, `dp_rgh_dxi_pa_m`, and other diagnostic terms. The gross `p_rgh`
and residual terms are excluded because raw `p_rgh` slopes are not friction in a
non-isothermal buoyant loop; mixing them into a loss chart is what made the
earlier AGENT-207 figure misleading.

## Units and sign convention

- All plotted quantities are in **Pa over the span** (integrated, not per-metre).
- **Mechanical losses** (friction, development/reset, minor) are always positive
  and are irreversible.
- **Buoyancy** is signed (`buoyancy_contribution_pa`, station-order convention).
  A negative value (downcomer, upper_leg) means the density-gradient force acts
  opposite to the reference positive flow direction — it DRIVES natural
  circulation and is a reversible driving head, not a loss. Figure 2 plots
  `|buoyancy|` as the bar length and keeps the sign in the text label.

## Encoding per figure

**Figure 1 (mechanical_loss_composition_by_span.svg)** — one stacked bar per span:
friction + development/reset + minor. The value label is the sum
(`mechanical_total_pa`).

**Figure 2 (buoyancy_drive_vs_resistance_by_span.svg)** — two bars per span:
green = `|buoyancy_signed_pa|` (label shows the signed value); blue =
`mechanical_total_pa`.

## Palette validation ({palette_result['mode']} surface {palette_result['surface']})

Colours were checked with `tools/analyze/palette_validator.py`:

```
{pal_lines}
  -> {"ALL PASS" if palette_result["ok"] else "FAILED"}
```

## Limitations

- All rows are `coarse_no_gci`; no mesh-independence/GCI uncertainty is attached.
- Minor-loss values are upper bounds (local dynamic-head normalization).
- Development/reset is zero for non-entry spans (test section, left upper).
- Recirculation spans (`left_lower_leg`, `left_upper_leg`, marked `*`) are
  diagnostic only — the single-stream friction interpretation is not valid there.
"""
    (output_dir / "DATA_DISCLOSURE.md").write_text(txt)


# ---------------------------------------------------------------------------
# README + summary
# ---------------------------------------------------------------------------

def write_readme(output_dir: Path, rows: list[dict]) -> None:
    n = len(rows)
    cases = ", ".join(CASE_LABELS.get(c, c) for c in CASE_ORDER)
    txt = f"""# Pressure Decomposition Figures — {TASK_ID}, 2026-07-09

Two clean SVG figures from the July 8 pressure term ledger, built from reusable,
data-disclosed scripts. Replaces earlier figures (AGENT-207, AGENT-233) that had
layout and encoding defects.

## Figures

- **`figures/mechanical_loss_composition_by_span.svg`** — horizontal stacked bars
  (friction | development/reset | minor-loss upper bound), one row per span,
  Salt 2/3/4 grouped under section headers, a value label on every bar.
- **`figures/buoyancy_drive_vs_resistance_by_span.svg`** — paired bars per span:
  buoyancy driving-term magnitude (green) vs total mechanical resistance (blue),
  each on its own baseline, buoyancy sign carried in the label.

## How this was made (reproducible)

1. Read the pressure term ledger (read-only); keep Salt 2/3/4 Jin rows.
2. Map ledger columns to plotted quantities — see `DATA_DISCLOSURE.md`.
3. Choose a categorical palette and **validate** it with
   `tools/analyze/palette_validator.py` (OKLCH lightness/chroma, Machado-2009 CVD
   ΔE, WCAG contrast). The build asserts PASS; the result is in `summary.json`.
4. Lay out with `tools/analyze/svg_chart_kit.py`: section-header rows for case
   grouping (no case/span label collision), recessive hairline grid, 2 px surface
   gaps between stacked segments, 4 px rounded data-ends, one legend, direct labels.
5. Write figures + `figure_data.csv` + `DATA_DISCLOSURE.md` + this README + `summary.json`.
6. Render to PNG and eyeball for collisions/overflow.

```bash
cd {REPO_ROOT}
python tools/analyze/build_pressure_decomposition_figures.py
python -m pytest tools/analyze/test_pressure_decomposition_figures.py tools/analyze/test_svg_chart_kit.py -q
# visual check (any SVG rasteriser):
convert -density 110 figures/mechanical_loss_composition_by_span.svg /tmp/fig1.png
```

## Reusable components

- **`tools/analyze/svg_chart_kit.py`** — dependency-free SVG horizontal-bar
  toolkit (theme tokens, scales, stacked bars, section headers, axis, legend,
  notes). Carries no project data; usable by any figure script in this repo.
- **`tools/analyze/palette_validator.py`** — Python port of the dataviz palette
  validator (importable `validate()` + CLI). Use it before shipping any palette.

## What was wrong before

- **AGENT-233 grouped chart** — three thin sub-bars per span all started at x=0,
  so the composition was invisible. Fixed by stacking.
- **AGENT-207 diverging chart** — buoyancy shared the zero origin with the
  mechanical stack, so positive buoyancy (heater, +5 Pa) was painted *on top of*
  the friction bar; the single downcomer −39 Pa also compressed the axis. Fixed
  by paired magnitude bars (Figure 2).
- **Both** collided the case label on top of the first span label. Fixed with
  section-header rows.

## Data provenance

| Field | Source |
|---|---|
| Pressure ledger | `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv` |
| {n} rows | {cases} (6 spans × 3 cases) |
| Entry flag fix | AGENT-197 (flow_reset_flag; dev=0 for test_section and left_upper) |
| Buoyancy sign audit | AGENT-230 |
| Readability diagnosis | AGENT-233 |

See `DATA_DISCLOSURE.md` for the exact column→visual mapping, units, sign
convention, palette-validation output, and limitations. See `figure_data.csv`
for every plotted value.
"""
    (output_dir / "README.md").write_text(txt)


def write_summary(output_dir: Path, rows: list[dict], palette_result: dict) -> None:
    cases = sorted({r["case"] for r in rows})
    spans = sorted({r["span"] for r in rows})
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": TASK_ID,
        "inputs": {"pressure_ledger": str(DEFAULT_INPUT.relative_to(REPO_ROOT))},
        "outputs": {
            "mechanical_composition_chart": "figures/mechanical_loss_composition_by_span.svg",
            "drive_vs_resistance_chart": "figures/buoyancy_drive_vs_resistance_by_span.svg",
            "figure_data": "figure_data.csv",
            "data_disclosure": "DATA_DISCLOSURE.md",
        },
        "reusable_modules": [
            "tools/analyze/svg_chart_kit.py",
            "tools/analyze/palette_validator.py",
        ],
        "column_map": COLUMN_MAP,
        "palette": {
            "friction": C_FRICTION, "dev_reset": C_DEV,
            "minor": C_MINOR, "buoyancy": C_BUOYANCY,
        },
        "palette_validation": {
            "ok": palette_result["ok"],
            "mode": palette_result["mode"],
            "surface": palette_result["surface"],
            "worst_cvd_delta_e": round(palette_result["worst_cvd"], 1),
            "report": [{"check": n, "state": s, "detail": d}
                       for n, s, d in palette_result["report"]],
        },
        "counts": {"rows": len(rows), "cases": len(cases), "spans": len(spans)},
        "case_ids": cases,
        "span_ids": spans,
        "limitations": [
            "All rows are coarse_no_gci; no GCI/mesh-independence bounds applied.",
            "Buoyancy term uses station-order sign convention; negative = drives downcomer flow.",
            "Minor-loss values are upper bounds (local dynamic-head normalization overestimates).",
            "Recirculation spans (left_lower_leg, left_upper_leg) are diagnostic only.",
            "Development/reset loss is zero for test_section_span and left_upper_leg (non-entry spans).",
        ],
        "replaced_figures": {
            "mechanical_pressure_terms_by_span.svg": "AGENT-233 — grouped sub-bars, composition illegible",
            "pressure_decomposition_by_span.svg": "AGENT-207 — overlapping marks at zero + scale compressed by downcomer buoyancy",
        },
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build(output_dir: Path, ledger_path: Path = DEFAULT_INPUT) -> dict:
    rows = extract_rows(read_ledger(ledger_path))
    if not rows:
        raise ValueError(f"No admitted rows found in {ledger_path}")

    # Verify the palette before drawing anything (data-disclosure discipline).
    palette_result = palette_validator.validate(PALETTE)
    if not palette_result["ok"]:
        raise ValueError("Palette failed validation:\n"
                         + palette_validator.format_report(palette_result, PALETTE))

    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")
    provenance = (f"{TASK_ID} · source pressure_term_ledger.csv · generated {stamp} · "
                  "values in figure_data.csv · see DATA_DISCLOSURE.md")

    build_mechanical_stacked(rows, figures_dir / "mechanical_loss_composition_by_span.svg", provenance)
    build_drive_vs_resistance(rows, figures_dir / "buoyancy_drive_vs_resistance_by_span.svg", provenance)
    write_figure_data(output_dir, rows)
    write_data_disclosure(output_dir, rows, ledger_path, palette_result)
    write_readme(output_dir, rows)
    write_summary(output_dir, rows, palette_result)

    result = {
        "output_dir": str(output_dir),
        "figures": [
            "figures/mechanical_loss_composition_by_span.svg",
            "figures/buoyancy_drive_vs_resistance_by_span.svg",
        ],
        "sidecars": ["figure_data.csv", "DATA_DISCLOSURE.md", "README.md", "summary.json"],
        "rows": len(rows),
        "palette_ok": palette_result["ok"],
    }
    print(json.dumps(result, indent=2))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args(argv)
    build(args.output_dir, args.ledger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
