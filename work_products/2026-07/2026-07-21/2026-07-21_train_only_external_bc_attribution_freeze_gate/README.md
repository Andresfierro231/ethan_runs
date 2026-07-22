---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/case_partition_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/freeze_readiness_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/residual_lane_readiness.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/README.md
tags: [forward-model, external-boundary, train-only, residual-attribution, freeze-gate]
related:
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/README.md
task: TODO-PRED-TRAIN-ONLY-EXTERNAL-BC-ATTRIBUTION-FREEZE-GATE-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Train-Only External BC Attribution Freeze Gate

## Decision

This package expands Fluid external-BC coverage from the prior one-row Salt2
smoke to all available canonical-train ambient-wall predictive rows. It keeps
heater, cooler, and test-section source/sink rows document-only. It does not
run Fluid, score validation/holdout/external rows, tune coefficients, select a
model, edit Fluid, or admit a closure.

Freeze is fail-closed: `no_candidate_frozen`.

## Results

- Canonical train cases: `4`.
- Requested train ambient-wall coverage rows: `16`.
- Available train ambient-wall rows: `12`.
- Missing train ambient-wall rows: `4`.
- Document-only source/sink rows: `9`.
- Parser failures on available dictionary rows: `0`.
- Full Fluid train solves run: `0`.
- Validation/holdout/external-test rows consumed: `0/0/0`.

## Outputs

- `segment_heat_path_coverage.csv`
- `document_only_source_sink_rows.csv`
- `train_fluid_solve_runtime_audit.csv`
- `train_residual_owner_scorecard.csv`
- `candidate_freeze_gate.csv`
- `validation_only_score_gate.csv`
- `holdout_external_test_release_gate.csv`
- `runtime_input_contract.csv`
- `fluid_state_snapshot.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Salt3/Salt4 legacy validation/holdout labels from older external-BC tables are
normalized to canonical final-training only for this train-only gate. Salt1
coverage is not synthesized. Realized CFD `wallHeatFlux`, CFD `mdot`, imposed
cooler duty, realized test-section heat, scored-row temperatures, and residual
fills remain forbidden runtime inputs. Residuals are not absorbed into F6,
hidden/global multipliers, external BC, or internal `Nu`.
