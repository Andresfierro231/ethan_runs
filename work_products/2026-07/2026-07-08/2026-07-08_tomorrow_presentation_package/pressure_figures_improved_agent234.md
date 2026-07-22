# Pressure Slide — Use The Improved AGENT-234 Figures

Date: 2026-07-09
Task: AGENT-234 (Claude)
Status: additive cross-reference — does not modify Codex-authored files in this package.

## What this is

The pressure-decomposition slide (Slide 3) and its support figure were built from
`work_products/.../2026-07-08_postprocessor_summary_charts/figures/`. Those SVGs
had layout/encoding defects (illegible grouped bars; a diverging chart that drew
buoyancy on top of the friction bar and compressed the axis; the case label
printed on top of the first span label). They have been redesigned.

Use these figures instead for the pressure slide:

| Slide role | Use this figure |
|---|---|
| Slide 3 primary — mechanical loss by span | `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/figures/mechanical_loss_composition_by_span.svg` |
| Slide 3 companion — driver vs resistance | `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/figures/buoyancy_drive_vs_resistance_by_span.svg` |

## Why they are better

- **Stacked composition** (Fig 1): each span is one bar whose segments show
  friction vs development/reset vs minor loss, with a total label — the
  composition is finally readable (the old grouped bars hid it).
- **Paired driver-vs-resistance** (Fig 2): buoyancy magnitude (green) and total
  mechanical resistance (blue) sit on separate baselines, so nothing overlaps.
  The downcomer's −39 Pa buoyancy visibly dominates all mechanical resistance —
  the real physical story, told without the broken diverging overlap.
- **Section headers** for Salt 2/3/4 remove the case/span label collision.
- **Validated palette** (dataviz checks all PASS) and full data disclosure:
  every plotted value is in `figure_data.csv`, and `DATA_DISCLOSURE.md` gives the
  exact column→visual mapping, units, and sign convention.

## Slide-safe wording (unchanged intent from AGENT-232)

Say:

> Once the reversible buoyancy driving term is separated from irreversible loss,
> the mechanical pressure-loss scale is comparable across the main legs
> (~1–13 Pa). In the downcomer the buoyancy driving head (~−39 Pa) dwarfs
> friction — it drives the loop; it is not a loss.

Avoid:

> The upper leg is responsible for the dominant pressure drop.

(That confuses a signed `p_rgh` / density-gradient driving term with irreversible
mechanical loss.)

## Provenance

- Figures + docs: `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/`
  (README.md, DATA_DISCLOSURE.md, figure_data.csv, summary.json)
- Builder: `tools/analyze/build_pressure_decomposition_figures.py`
- Reusable toolkit: `tools/analyze/svg_chart_kit.py`, `tools/analyze/palette_validator.py`
- Source data: `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
