---
provenance:
  generated_by: tools/analyze/build_m0_setup_only_baseline_prediction_scorecard.py
  task_id: TODO-M0-SETUP-ONLY-BASELINE-PREDICTION-SCORECARD-2026-07-22
  generated_at_utc: 2026-07-22T13:24:51.230943+00:00
task: TODO-M0-SETUP-ONLY-BASELINE-PREDICTION-SCORECARD-2026-07-22
tags:
  - M0
  - setup-only
  - scorecard
  - forward-prediction
related:
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/prediction_join_shell.csv
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/baseline_model_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_model_execution_path/staged_implementation_plan.csv
---

# M0 Setup-Only Baseline Prediction Scorecard

## Decision

M0 is publishable as a lower-bound setup-only scorecard shell, but not as a
numerical final prediction. The current evidence has no frozen runtime-legal
prediction artifact, so every target row is retained with an explicit
`missing_no_frozen_runtime_legal_runner` label.

## Result

- Scorecard target rows: `79`.
- Cases represented: `12`.
- Metrics represented: `7`.
- Numerical prediction rows: `0`.
- Missing prediction rows: `79`.
- Runtime leakage failures: `0`.

## Scientific Use

Use this package as the comparison baseline for later model forms. It prevents
future analyses from silently omitting targets, mixing split roles, or using
protected CFD/validation quantities at runtime. It does not claim an admitted
closure, final score, or predictive accuracy.

## Guardrails

No Fluid/OpenFOAM solve, scheduler action, fitting, model selection,
source/property release, final score claim, native-output mutation, registry
mutation, external edit, S11/S12/S13/S15/S6 trigger, hidden multiplier, or
residual absorption into internal Nu was performed.
