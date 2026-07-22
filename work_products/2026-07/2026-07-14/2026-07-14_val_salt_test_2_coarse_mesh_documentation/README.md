---
provenance:
  - imports/2026-05-29_val_salt_test_2_coarse_mesh_laminar_import.json
  - jadyn_runs/salt2/2026-06-01_continuation_candidate/README.md
  - jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml
  - jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T
  - jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/case_config.yaml
  - jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/0/T
  - work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_steady_state_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/case_bc_response_matrix.csv
tags: [cfd-pp, salt2, boundary-conditions, provenance, rcExternalTemperature]
related:
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/salt2_jin_vs_val_comparison.csv
task: AGENT-354
date: 2026-07-14
role: Writer/Implementer
type: work_product
status: complete
---
# val_salt_test_2_coarse_mesh Documentation Package

## Purpose

This package documents `val_salt_test_2_coarse_mesh`, the requested canonical
display label for the existing `2026-06-01_continuation_candidate` /
`val_salt_test_2_coarse_mesh_laminar` lineage. It does not rename directories,
edit registry state, mutate native CFD outputs, or write external
`../cfd-modeling-tools` files.

## Main Findings

- Display migration: use `val_salt_test_2_coarse_mesh` in new prose and tables,
  while preserving `val_salt_test_2_coarse_mesh_laminar` as the historical
  `source_id` and
  `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation`
  as the continuation provenance path.
- The val lineage is distinct from `salt2_jin`; it is not a mislabeled Jin
  continuation. Salt2 Jin remains the current mainline Salt2 comparison row.
- Both cases are closed-loop OpenFOAM cases: no inlet/outlet patch was found in
  `0/U` or `0/p_rgh`; velocity is default `noSlip` with NCC connector `slip`,
  and pressure is `fixedFluxPressure`.
- Thermal BCs use lower-leg heater patches, a separate powered test-section
  patch, fixed-Q upper cooler/reducer patches, and passive wall/stub exchange.
- `rcExternalTemperature` carries `Ta`, `Tsur`, `emissivity`, wall-layer
  coefficients, and optional `Q`. Current repo guidance says radiation is folded
  into total `wallHeatFlux`; no separate exported `qr` term is available.
- Material evidence is available from `case_config.yaml` and
  `constant/physicalProperties`: laminar Hitec salt family, `heRhoThermo`,
  `icoTabulated` transport, `hPolynomial` Cp, `icoPolynomial` density,
  `momentumTransport` laminar, and Fourier laminar thermal transport.
- Salt2 Jin is current mainline nominal evidence with hydraulic-stationary /
  heat-drifting caveat. Val is historical/diagnostic or blocked context unless a
  future row explicitly re-admits it.

## Files

- `lineage_migration_plan.csv`: display-label migration and provenance path plan.
- `boundary_condition_summary.csv`: grouped thermal, velocity, pressure, and
  inlet/outlet boundary facts.
- `boundary_condition_patch_detail.csv`: patch-level thermal BC extraction from
  `0/T`.
- `material_property_evidence.csv`: fluid, property, transport, and material
  evidence.
- `salt2_jin_comparison.csv`: comparison report versus current Salt2 Jin.
- `source_manifest.csv`: exact read-only inputs and generated outputs.
- `summary.json`: machine-readable package summary.

## Counts

- Boundary summary rows: `18`
- Patch detail rows: `138`
- Material/property rows: `18`
- Comparison rows: `18`
