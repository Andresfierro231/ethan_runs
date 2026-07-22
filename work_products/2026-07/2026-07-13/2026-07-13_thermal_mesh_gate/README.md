# Thermal Mesh Gate

Task: `TODO-PRED-THERMAL-MESH-GATE`

Generated: `2026-07-13T17:06:52-05:00`

## Purpose

This package consumes the repaired Salt2 medium and fine thermal segment outputs
and decides whether thermal UA/HTC/Nu can move from repair-smoke evidence into
mesh/GCI or closure-admission use.

## Result

- QOI rows: `7`
- Two-level medium/fine-complete rows: `5`
- Fit-admissible rows: `0`
- Publication-ready thermal GCI rows: `0`
- Main status: `blocked_sign_review_and_missing_coarse_triplets`

The old blocker, missing fine reconstructed-`T`, is resolved. The current
blockers are sign review, missing coarse thermal triplets, and downcomer policy.

## Outputs

- `thermal_mesh_gate_qois.csv`: per-segment medium/fine QOI values and gate decisions.
- `thermal_mesh_gate_evidence.csv`: source smoke/package evidence.
- `thermal_mesh_gate_blockers.csv`: non-admitted rows and next actions.
- `summary.json`: machine-readable counts and source paths.

## Interpretation Boundary

These rows are not closure-fit targets. `fit_admissible=yes` is intentionally
zero until sign, heat-balance, downcomer policy, and coarse/medium/fine thermal
triplet gates are resolved.
