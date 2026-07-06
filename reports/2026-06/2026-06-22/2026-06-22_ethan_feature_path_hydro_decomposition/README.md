# Ethan Feature-Path Hydro Decomposition

Generated: `2026-06-22`

## Purpose

This package freezes the current retained-time feature-path hydraulic signal in
the strongest additive form the repo already preserves:

- exact endpoint-patch `p` and `p_rgh` differences from
  `raw_extraction/feature_patch_pressure_timeseries.csv`
- the existing same-boundary local straight reference from the June 19 Salt
  feature hardening package
- the June 22 wall-window hydro probe as a comparison surface rather than the
  primary decomposition

## Current outcome

- feature case rows: `45`
- fit-ready case rows: `21`
- dominant method status: `defended_patch_endpoint_prgh_local_boundary_reference`

## Interpretation boundary

This package **does** defend the patch-endpoint path decomposition:

- `dp_feature_prgh_pa` is taken directly from the preserved patch endpoints
- `dp_feature_hydro_path_pa = dp_feature_p_pa - dp_feature_prgh_pa`

It still does **not** claim a continuous field-integrated density path. The
straight subtraction remains the local-boundary gradient reference already used
in the June 19 feature package. That is enough to reopen the feature hardening
lane, but not enough to claim a new CFD observable has been extracted.
