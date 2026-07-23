---
provenance:
  generated_by: codex
  task_id: TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22
  date: 2026-07-22
tags:
  - passive-h2
  - salt1
  - mesh-area
  - source-property
  - handoff
related:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/README.md
  - .agent/status/2026-07-22_TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22.md
  - .agent/journal/2026-07-22/passive-h2-salt1-mesh-area-provenance-repair-preflight.md
---

# Passive-H2 Salt1 Mesh-Area Provenance Repair Preflight

## Why This Exists

PASSIVE-H2 needed Salt1 source-family area provenance that did not depend on
native wallHeatFlux diagnostics. This row tested whether the recovered Salt1
operator areas can be rebuilt from setup-only mesh geometry.

## Open First

- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/family_area_reconciliation.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/release_preflight_gate.csv`
- `tools/analyze/build_passive_h2_salt1_mesh_area_provenance_repair_preflight.py`

## Trusted Inputs

- Salt1 setup mesh:
  `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/constant/polyMesh/{boundary,faces,points}`
- Salt1 setup temperatures:
  `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/0/T`
- Recovered five-family operator:
  `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background/salt1_five_family_operator_rows_for_fluid.csv`

## Result

Decision: `salt1_mesh_area_provenance_fail_closed_no_release_no_score`.

All `39` required patches were found. Four of five families reconcile to the
recovered operator areas within tolerance. `junction` fails, so the five-family
mesh-area-backed operator is not ready. No source/property release, freeze, or
score was emitted.

## Next Task Sequence

1. Audit the `junction` patch grouping and recovered area source against setup
   mesh geometry.
2. Decide whether the mismatch is a recoverable grouping/tolerance issue or a
   hard provenance break.
3. If recovered, rebuild a five-family area-backed operator candidate and rerun
   source/property release and same-QOI UQ gates under a new claimed row.

## Output Contract

Any successor must preserve patch-level source paths, family-level area
reconciliation, release-gate rows, and explicit no-score/no-freeze flags until
all gates pass.

## Do Not Do

Do not mutate native solver outputs. Do not use realized wallHeatFlux, Qwall,
CFD mdot, validation temperatures, imposed cooler duty, or realized
test-section heat as runtime inputs. Do not score validation/holdout/external
rows, freeze coefficients, edit Fluid/external repos, change registry/admission
state, or claim source/property release from this preflight alone.
