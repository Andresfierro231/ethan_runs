---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/train_solve_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/thermal_residual_attribution.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s12_thermal_shape_ownership_candidate/admission_gate_matrix.csv
tags: [forward-model, s12, train-only, score-gate, no-freeze]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-F-S12-HIAX1-TRAIN-SCORE-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-external-bc-phase-f-s12-hiax1-train-score.md
task: TODO-FLUID-EXTERNAL-BC-PHASE-F-S12-HIAX1-TRAIN-SCORE-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# S12-HIAX1 Phase F Train Score Gate

This package computes finite train-only metrics from the completed Phase E
Fluid external-boundary solve and applies them to the S12-HIAX1 score gate.

## Result

- finite train metrics are available from legal train-only evidence;
- S12-HIAX1 itself is not scored as an implemented candidate;
- no freeze, admission, validation score, holdout score, or external-test score
  is released.

## Key Metrics

- predicted train mdot: `0.00626567502344` kg/s
- reference train mdot: `0.0168` kg/s
- pressure residual: `-1.30168709234e-06` Pa
- TP RMSE: `80.4586` K
- TW RMSE: `84.6487` K
- all-probe RMSE: `83.3619` K

## Interpretation

The finite metrics are a train-only precursor score from the Phase E external
boundary solve. They do not release S12-HIAX1 because exchange-state QOIs,
same-QOI UQ, attribution freeze, and source/property release remain fail-closed.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, blocker register, generated documentation index, thesis chapter,
validation row, holdout row, or external-test row was modified or consumed.
