# Data Disclosure — Pressure Decomposition Figures (AGENT-234)

This file states exactly what data goes into each figure. Nothing plotted is
hidden or silently transformed. Every plotted value is also in
`figure_data.csv` (one row per span/case).

## Single source

- **Input:** `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- **Rows used:** 18 = 3 cases × 6 spans
  (Salt 2/3/4 Jin mainline). Salt 1 Jin is excluded (weakly converged).
- **No new CFD extraction.** The ledger is read-only; figures are a presentation
  of already-audited values.

## Ledger column → visual element

| Ledger column | Role in the figures |
|---|---|
| `distributed_friction_pa` | friction segment (fig 1 & 2) |
| `development_loss_pa` | development/reset segment (fig 1 & 2) |
| `minor_loss_pa` | minor-loss upper-bound segment (fig 1 & 2) |
| `buoyancy_contribution_pa` | buoyancy driving term, signed (fig 2) |
| `recirculation_flag` | asterisk / italic label on recirculation spans |
| `Re` | context only (not plotted; disclosed in figure_data.csv) |

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

## Palette validation (light surface #fcfcfb)

Colours were checked with `tools/analyze/palette_validator.py`:

```
  [PASS] Lightness band: all 4 inside L 0.43-0.77
  [PASS] Chroma floor: all >= 0.1
  [PASS] CVD separation: worst adjacent #eb6834<->#2a78d6 ΔE 96.7 (protan)
  [PASS] Contrast vs surface: all >= 3.0:1
  -> ALL PASS
```

## Limitations

- All rows are `coarse_no_gci`; no mesh-independence/GCI uncertainty is attached.
- Minor-loss values are upper bounds (local dynamic-head normalization).
- Development/reset is zero for non-entry spans (test section, left upper).
- Recirculation spans (`left_lower_leg`, `left_upper_leg`, marked `*`) are
  diagnostic only — the single-stream friction interpretation is not valid there.
