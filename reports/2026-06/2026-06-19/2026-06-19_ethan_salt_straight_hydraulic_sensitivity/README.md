# Ethan Salt Straight Hydraulic Sensitivity

Generated: `2026-06-19`

## Purpose

This package rebuilds retained-time hydro-corrected straight-section rows from
the preserved Salt case-analysis package roots, then keeps the late-window
sensitivity result honest when the retained tail is shorter than the target
approximately `20 s`.

## Inputs

- `reports/2026-06-18_ethan_salt_model_dependency_package/hydraulic_hardening_audit.csv`
- `reports/2026-06-18_ethan_salt_model_dependency_package/hydraulic_fit_ready_rows.csv`
- `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_dashboard.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_cumulative_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/leg_centerline_station_definitions.csv`

## Important boundary

The preserved additive package roots now support explicit retained-time straight
rows, but the currently published Salt package roots only preserve about `3-5 s`
of tail data. The package therefore upgrades the blocker from "no retained-time
rows exist" to the narrower statement that a true last-`20 s`
window still needs continuation-derived retained support before the late-window
sensitivity can be called complete.
