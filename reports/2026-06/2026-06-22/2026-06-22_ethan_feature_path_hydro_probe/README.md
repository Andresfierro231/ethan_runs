# Ethan Feature-Path Hydro Probe

Generated: `2026-06-22`

## Purpose

This package builds a fresh additive retained-time probe for the Salt feature
hydraulic blocker. It reconstructs endpoint-adjacent wall `p` and `p_rgh`
windows from the preserved June 15 wall-face samples and reports what those
windows imply for the still-blocked hydro term.

The package is deliberately scoped as a probe:

- it does **not** edit any shared extractor
- it does **not** claim a defended full feature-path hydro integral
- it does **not** promote feature `K_eff`

## Inputs

- `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_dashboard.csv`
- `reports/2026-06-18_ethan_salt_closure_correlation_package/salt_feature_correlation_inputs.csv`
- `reports/2026-06-19_ethan_salt_feature_hydraulic_hardening/feature_hydro_closure_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/feature_minor_loss_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/raw_extraction/leg_wall_face_geometry.csv`
- `tmp/2026-06-15_live_case_analysis/**/raw_extraction/leg_wall_face_samples.csv`

## Window rule

- endpoint window size: `3` nearest unique `s_span_m` stations on each adjacent span side
- endpoint-to-endpoint wall window deltas are area-weighted across the selected face rows
- the hydro candidate reported here is `Delta p_wall - Delta p_rgh_wall` from those endpoint windows

## Output tables

- `feature_path_hydro_probe_timeseries.csv`
  One retained-time row per case-feature with both endpoint windows, wall means,
  and the hydro-correction candidate.
- `feature_path_hydro_probe_case_summary.csv`
  One case-feature summary row with coverage and consistency counts.
- `feature_path_hydro_probe_feature_summary.csv`
  Aggregated feature-family view across the Salt cases.
- `feature_path_hydro_probe_blockers.csv`
  The remaining interpretation boundary and why this probe stops short of a defended fit.

## Counts

- case-feature rows: `45`
- retained-time rows: `185`
- probe-ready rows: `185`
- partial rows: `0`
- blocked rows: `0`
