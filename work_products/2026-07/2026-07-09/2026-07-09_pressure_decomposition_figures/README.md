# Pressure Decomposition Figures — AGENT-234, 2026-07-09

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
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
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
| 18 rows | Salt 2, Salt 3, Salt 4 (6 spans × 3 cases) |
| Entry flag fix | AGENT-197 (flow_reset_flag; dev=0 for test_section and left_upper) |
| Buoyancy sign audit | AGENT-230 |
| Readability diagnosis | AGENT-233 |

See `DATA_DISCLOSURE.md` for the exact column→visual mapping, units, sign
convention, palette-validation output, and limitations. See `figure_data.csv`
for every plotted value.
