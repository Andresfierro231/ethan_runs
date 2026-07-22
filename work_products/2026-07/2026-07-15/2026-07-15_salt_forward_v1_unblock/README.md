---
provenance:
  task: AGENT-402
  generated_by: codex
tags: [salt, cfd-pp, forward-v1, unblock, training-data, pm5, scheduler]
related:
  - operational_notes/07-26/14/2026-07-14_SALT_TRAINING_TESTING_EVIDENCE_ROLLOUT.md
  - operational_notes/07-26/14/2026-07-14_TOMORROW_FORWARD_V1_FULL_CONTEXT_AND_OVERNIGHT_PLAN.md
  - work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/README.md
---
# Salt Forward-v1 Unblock

This package implements the July 15 first-pass unblock plan for Salt CFD and
forward-v1. It does not admit final forward-v1 and does not mutate native CFD
outputs. It organizes what can be used now, what is still blocked, and the
next concrete actions.

## Current State

- Corrected-Q continuation job `3293924` is still running.
- Dependent Salt2/Salt4 selected harvester `3295438` is still pending on
  dependency.
- PM5 batch jobs `3295901` and `3295968` were cancelled before running.
- PM5 interactive run `interactive_3295120_retry2` completed, but all 12 parsed
  matched-plane rows are incomplete because required sampled fields are missing.
- Salt thermal training can proceed with six rows; Salt2 +/-5Q remains holdout.

## Use Now For Thermal Closure Work

Use `salt_training_fit_input_table.csv` as the current compact case list:

- Training: `salt1_jin_nominal_continuation_corrected`,
  `salt1_jin_lo10q_corrected`, `salt1_jin_hi10q_corrected`, `salt4_jin`,
  `salt4_jin_lo5q_corrected`, `salt4_jin_hi5q_corrected`.
- Holdout/testing: `salt2_jin_lo5q_corrected`,
  `salt2_jin_hi5q_corrected`.

Guardrails:

- Keep Q-perturbed rows labeled as perturbed-Q.
- Do not use Salt2 +/-5Q for fitting or model selection.
- Salt1 hi10q is superseded for thermal training use by the terminal harvest
  and patch-complete BC evidence.

## PM5 Status

PM5 is not waiting on a scheduler job anymore. The current blocker is an
extraction/sampling contract problem:

- 4 parsed CSVs exist.
- 12 rows exist.
- 0 rows have populated `Re`, `bulk_T_K`, or `wallHeatFlux_W_m2`.
- All rows carry `blocked-missing-field`.

Do not relaunch the same PM5 script unchanged. First fix the sampled-field
contract so the plane outputs include `U/rho/T` and the wall-band outputs
include wall `T` and `wallHeatFlux`.

## Thermal/HX And Sensor Notes

AGENT-391 produced a completed setup-only cooler bakeoff. The best currently
available setup-legal candidate is `salt2_fit_constant_UA_bulk_drive`:

- all non-Salt1 RMSE: `4.63756559107 W`
- Salt3 validation absolute error: `2.86910400386 W`
- Salt4 holdout absolute error: `7.50261861283 W`

This is an important candidate, but it still needs scorecard integration and
runtime-input audit before final forward-v1 admission.

AGENT-392 also completed its thermal overnight rescue package with all 8 stages
at exit code `0`, including `setup_only_hx_fit` and `setup_only_hx_tests`. Treat
that package as the next cited input for a scorecard refresh, not as automatic
final forward-v1 admission.

Sensor policy remains target-only:

- 15 sensors are provisional diagnostic-scoreable.
- `TP2` and `TW10` remain blocked.
- Sensor temperatures must not be runtime inputs.

## Files

- `scheduler_snapshot.csv`: current job state and next action.
- `pm5_matched_plane_recovery_audit.csv`: PM5 parsed output audit.
- `salt_training_fit_input_table.csv`: split-aware thermal closure input table.
- `stale_inventory_refresh_actions.csv`: stale labels/docs to refresh.
- `setup_only_hx_boundary_action_table.csv`: thermal/HX action state.
- `sensor_policy_action_table.csv`: score/exclusion policy for TP/TW sensors.
- `source_manifest.csv`: exact input and generated paths.
- `summary.json`: machine-readable closeout summary.
