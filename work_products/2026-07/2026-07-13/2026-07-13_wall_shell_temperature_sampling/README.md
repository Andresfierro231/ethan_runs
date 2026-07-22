# Wall-Shell Temperature Sampling

Generated: `2026-07-13T21:45:57+00:00`
Task: `TODO-PRED-WALL-SHELL-SAMPLE`

## Purpose

This package fills the main TODO-PRED-WALL-LAYER blocker by deriving a local
near-wall temperature proxy from reconstructed OpenFOAM 13 cases. The proxy is
not a new solver result. It is the internal owner-cell temperature immediately
behind each boundary face on an `rcExternalTemperature` patch.

## Proxy Definition

`T_wall_shell_K = mean(T_internal[owner[boundary_face]])`

Patch rows report boundary face count, owner sample count, unique owner-cell
count, min/max/std, and exact reconstructed field/mesh paths. Segment rows are
area-weighted with AGENT-263 patch areas. Treat this as a first-cell
patch-internal shell proxy, not as an independent wall-function or y-plus
resolved thermal profile.

## Outputs

- `patch_wall_shell_temperatures.csv`
- `segment_wall_shell_temperatures.csv`
- `run_metadata.json`

## Key Counts

- Patch rows: `108`
- Segment rows: `21`
- Blocked patch rows: `0`

## Use In Parity

These segment rows are intended to be consumed by
`tools/analyze/build_wall_layer_drive_mapping.py` so E1 wall-shell replay can be
computed. E2 blend fitting remains diagnostic unless a later package admits a
family-level beta with validation separation.
