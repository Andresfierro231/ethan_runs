# Water Thermal Closure Readiness

Generated: `2026-06-19`

## Purpose

This package turns the Water-family thermal support and enthalpy artifacts into
a closure-readiness table. It does not claim any defended Water Nu dependency.

## Inputs

- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/water_effective_htc_nu_fields.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/enthalpy_balance_by_leg.csv`
- `reports/2026-06-19_ethan_water_phase1_starter_package/water_hydraulic_branch_readiness.csv`

## Interpretation boundary

Rows are labeled only as readiness outcomes:
- `closure_rebuild_priority`
- `closure_rebuild_candidate`
- `support_present_context_only`
- `blocked_*`
