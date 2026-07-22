---
provenance:
  - registry/salt2/native_2d_cfd_external/salt_test_2/val_salt_test_2_coarse_mesh_laminar/aggregates/wall_heat_flux_grouped.csv
  - registry/salt2/native_2d_cfd_external/salt_test_2/val_salt_test_2_coarse_mesh_laminar/aggregates/case_summary.csv
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/boundary_condition_summary.csv
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/material_property_evidence.csv
  - work_products/2026-07/2026-07-09/2026-07-09_cfd_steady_state_continuation_table/all_timeseries_case_rollup.csv
tags: [cfd-pp, salt2, val-salt2, admission, heat-loss-ledger]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/README.md
task: AGENT-422
date: 2026-07-15
role: cfd-pp/Thermal-admission/Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt_test_2_coarse_mesh Postprocessing Admission Unlock

## Observed Facts

- Refreshed terminal window: `8302` to `8602` s.
- Refreshed steady-state label: `steady`.
- Latest `total_Q_postProc`: `0.193062` W.
- mdot consensus from registry summary: `0.01361622898` kg/s.
- Maximum heat linear drift over the terminal window: `0.0132872` W.
- Maximum mdot relative linear drift over the terminal window: `7.9509e-05`.
- BC/source/material contract rows attached: `36`.
- Section heat-loss ledger rows: `14`.

## Interpretation

`val_salt_test_2_coarse_mesh` is no longer blocked by a missing section
heat-loss ledger. The older `hydraulic_stationary_heat_drifting` label is
superseded for this admission pass by the refreshed terminal-window check over
the existing registry wallHeatFlux and mdot tails. The older drift label remains
useful context because low-noise monotonic sub-watt heat terms can trip a
ratio-style detector, but the magnitude is small relative to the case heat
budget.

## Admission Refresh

- Admission decision: `external_test_validation_candidate_unlocked`.
- Split role: `external_test_or_validation_candidate`.
- Usable now: `yes_external_test_validation`.
- Guardrail: do not fit or tune on this row if it is used as blind external
  test data. Realized CFD `wallHeatFlux` is admissible as diagnostic/scoring
  evidence, not as a predictive runtime input.

## Files

- `refreshed_terminal_steady_state_gate.csv`
- `val_salt2_section_heat_loss_ledger.csv`
- `val_salt2_bc_source_material_contract.csv`
- `val_salt2_split_admission_refresh.csv`
- `evidence_conflict_resolution.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry state, scheduler state, generated indexes, or
external Fluid files were mutated. This package consumes existing
postprocessing/registry evidence only.
