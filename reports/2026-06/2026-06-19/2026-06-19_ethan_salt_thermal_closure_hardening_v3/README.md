# Ethan Salt Thermal Closure Hardening v3

Generated: `2026-06-19`

## Purpose

This package reuses the exact retained-time Salt thermal closure machinery from
the June 19 v2 hardening pass, but applies a more explicit moderate-domain Nu
admission rule. It is still closure-first: unresolved residual remains a
reported quantity rather than something hidden inside `Nu`.

## Inputs

- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/enthalpy_balance_by_leg.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/fluid_side_htc_nu_section_summary.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/bulk_vs_centerline_temperature_correction.csv`
- `reports/2026-06-18_ethan_salt_analysis_checkpoint_suite/phase3_branch_trust_gate/branch_promotion_gate.csv`
- `tmp/2026-06-15_live_case_analysis/**/azimuthal_wall_transport_summary.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_cumulative_timeseries.csv`

## Moderate-domain gates

- support fraction remains at least `0.90`
- minimum `|Twall - Tbulk|` remains `0.25 K`
- residual fraction ceiling is now `0.45`
- grouped reconstruction ceiling remains `0.05`
- `right_leg` remains blocked
- derived `upcomer` remains sensitivity-only

## Current outcome

- direct fit-ready rows: `7`
- fit-ready branches: `left_lower_leg`

## Interpretation boundary

Any defended Salt Nu claim from this package is necessarily domain-limited to
the direct branches that survive these gates. Rows outside that domain remain
explicitly classified, not silently discarded.
