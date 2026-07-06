# Ethan Salt Feature-Path Hydraulic Hardening

Generated: `2026-06-19`

## Purpose

This package converts the current Salt feature proxy closure into an explicit
feature-path blocker audit. It does **not** claim a defended full feature-path
hydro integral. Instead, it maps each feature row onto a machine-readable
status showing whether the repo currently has only a proxy endpoint method or
an outright support failure.

## Inputs

- `reports/2026-06-19_ethan_salt_feature_hydraulic_hardening/feature_hydro_closure_timeseries.csv`
- `reports/2026-06-19_ethan_salt_feature_hydraulic_hardening/feature_hydro_closure_by_case.csv`
- `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_dashboard.csv`

## Current outcome

- case rows: `45`
- fit-ready defended feature rows: `0`
- dominant method status: `full_path_missing_proxy_only_available`

## Interpretation boundary

This package is intentionally conservative. Proxy-positive rows remain
`sensitivity_only` until a retained-time feature-path hydro integral is
available. The downstream v3 Salt dependency package must not publish a
defended feature `K_eff` model from these rows.

The retained-time table now preserves the proxy decomposition explicitly:

- `dp_feature_loss_prgh_endpoint_pa`
- `dp_feature_hydro_endpoint_proxy_pa`
- `feature_excess_proxy_pa`
