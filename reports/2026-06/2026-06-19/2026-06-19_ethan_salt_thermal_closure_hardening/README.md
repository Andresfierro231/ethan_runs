# Ethan Salt Thermal Closure Hardening

Generated: `2026-06-19`

## Purpose

This package rebuilds Salt branch/leg thermal closure from exact retained-time
enthalpy rows and exact retained-time section wall-heat rows, then decomposes
the wall exchange into intended-transfer, parasitic-loss, sink, grouped
reconstruction gap, and closure residual buckets. It is an audit-first package:
rows remain excluded unless support, sign, and residual gates are all met.

## Inputs

- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/enthalpy_balance_by_leg.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/fluid_side_htc_nu_section_summary.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/bulk_vs_centerline_temperature_correction.csv`
- `reports/2026-06-18_ethan_salt_analysis_checkpoint_suite/phase3_branch_trust_gate/branch_promotion_gate.csv`
- `tmp/2026-06-15_live_case_analysis/**/azimuthal_wall_transport_summary.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_cumulative_timeseries.csv`

## Key counts

- case count: `9`
- time row count: `259`
- case row count: `63`
- fit-ready branch rows: `2`

## Gate logic

- `right_leg` stays hard-blocked
- `upcomer` stays sensitivity-only because it is derived from overlapping direct spans
- direct branches require:
  - support fraction at least `0.90`
  - `|Twall - Tbulk|` at least `0.25 K`
  - mean residual fraction at most `0.30`
  - pass-time fraction at least `0.75`
  - consistent enthalpy vs wall-heat direction

## Important limitation

This package still does **not** resolve a full internal convection / wall
conduction / external convection-radiation resistance split. It keeps those
unknowns separated into explicit buckets instead of hiding them inside Salt-side
`Nu`.
