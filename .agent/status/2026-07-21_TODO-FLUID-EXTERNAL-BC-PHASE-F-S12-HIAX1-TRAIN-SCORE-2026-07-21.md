---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/finite_train_metric_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/s12_hiax1_train_score_gate.csv
tags: [forward-model, s12, train-only, score-gate, no-freeze]
related:
  - .agent/journal/2026-07-21/fluid-external-bc-phase-f-s12-hiax1-train-score.md
  - imports/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/README.md
task: TODO-FLUID-EXTERNAL-BC-PHASE-F-S12-HIAX1-TRAIN-SCORE-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: status
status: complete
---
# S12-HIAX1 Phase F Train Score Status

Built a train-only S12-HIAX1 score-gate package from the completed Phase E
Fluid external-boundary solve.

## Changes Made

- Created `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/`.
- Added a reproducible builder and checker for the S12 Phase F package.
- Emitted finite train-only metrics:
  - predicted mdot `0.00626567502343775 kg/s`;
  - reference mdot `0.0168 kg/s`;
  - mdot residual `-0.010534324976562249 kg/s`;
  - pressure residual `-1.3016870923365786e-06 Pa`;
  - TP RMSE `80.4585733904668 K`;
  - TW RMSE `84.64865165641251 K`;
  - all-probe RMSE `83.36187927489736 K`.
- Emitted `freeze_decision.csv` with `decision=do_not_freeze`.
- Preserved S12 blockers: exchange-state evidence, same-QOI UQ,
  source/property release, and candidate-level scoring remain closed for
  S12-HIAX1 itself.

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/build_phase_f_s12_hiax1_train_score.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/check_phase_f_s12_hiax1_train_score.py`
  passed.
- A parallel checker attempt was discarded because it raced the generator while
  files were being rewritten; the sequential checker run after generation
  passed.

## Guardrails

No native CFD/OpenFOAM output mutation, registry/admission mutation, scheduler
action, OpenFOAM solver/postprocessing/sampler/harvest launch, Fluid source
edit, external edit, validation scoring, holdout scoring, external-test scoring,
fitting/tuning/model selection, candidate freeze, source/property release,
final predictive admission, blocker-register change, generated-index refresh,
thesis edit, or residual absorption into internal `Nu` was performed.
