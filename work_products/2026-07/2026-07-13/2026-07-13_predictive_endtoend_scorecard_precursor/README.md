---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/hx_validation_guardrail_scorecard.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/decision_summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_forward_v0_solve_case_compute_run/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/summary.json
tags: [forward-model, predictive-1d, scorecard, hydraulic-guardrail, validation-split]
related:
  - .agent/status/2026-07-13_AGENT-303.md
  - .agent/journal/2026-07-13/predictive-endtoend-scorecard-precursor.md
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-303
date: 2026-07-13
role: Implementer/Writer
type: work_product
status: complete
---
# Predictive End-to-End Scorecard Precursor

This package assembles the forward-v1 readiness/scorecard precursor from
completed predictive lanes. It performs no new thermal fitting, does not edit
native CFD outputs, and does not edit external Fluid source.

## Result

Forward-v1 is not ready for an end-to-end claim. The current evidence supports a
guardrailed scorecard precursor:

- The strict predictive input contract passes: 32 runtime fields, 3 mainline
  Salt case rows, 75 validation targets, and 0 violations.
- The split is locked: `salt_2` train, `salt_3` validation, `salt_4` holdout;
  `salt1_nominal` remains diagnostic-only; corrected-Q and low-heat rows remain
  blocked.
- HX1 one-scalar rows can be reported as proxy, guardrailed scores. For
  `F1_heater_only`, abs HX-duty error is `0.000 W` on train, `2.341 W` on
  validation, and `17.511 W` on holdout.
- Hydraulic readiness fails: both forward-v0 variants overpredict mdot for
  every Salt row. The hydraulic gate reports F1 mean mdot error `36.37%` vs CFD.
- Hydraulic correction candidates now exist: AGENT-300 ranks
  `H1_localized_named_loss_and_reset_bundle` first and reports mean required
  resistance multiplier `2.115`, but this still needs a bounded forward rerun.
- Full `solve_case` confirmation is submitted as Slurm job `3293960` and was
  last recorded `RUNNING`; it is not harvested.
- Sensor map scoring is partially available after solve: AGENT-302 maps 17
  labels, with 15 provisionally diagnostic-scoreable and `TP2`/`TW10` blocked.
- Thermal mesh admission remains blocked: 7 Salt2 QOI rows, 5 two-level-complete
  rows, 0 fit-admissible rows, and 0 publication-ready thermal GCI rows.

## Files

- `readiness_lanes.csv`: lane-level readiness, score permissions, blockers, and
  next gates.
- `split_scorecard_precursor.csv`: six Salt2/Salt3/Salt4 x F0/F1 rows copied
  from the split-aware HX/hydraulic guardrail scorecard.
- `residual_attribution_precursor.csv`: row-level residual attribution separated
  into hydraulic, HX/cooler, thermal-state, passive-wall, solve_case, and sensor
  lanes.
- `blockers.csv`: precursor-specific blocker table.
- `source_manifest.csv`: exact source artifacts and mutation status.
- `summary.json`: machine-readable package summary.

## Scoring Boundary

Rows in `split_scorecard_precursor.csv` are valid as precursor/proxy rows only.
They are not final forward-v1 scores because the full Fluid `solve_case` path
has not been run and the hydraulic guardrail fails. The training row is not a
model-selection score. Salt3 is the validation row after the Salt2-trained scalar
is frozen. Salt4 is held out until model form and validation decisions are
frozen.

## Residual Attribution

Do not collapse residuals into a single thermal correction. This package keeps
the active residual lanes separate:

- hydraulic: mdot overprediction blocks end-to-end readiness;
- HX/cooler: scored via HX1 one-scalar duty error under the locked split;
- source contract: F0 versus F1 separates current Fluid source behavior from
  heater-only source behavior;
- passive wall: E1/E2 wall-shell modes are executable but diagnostic only;
- thermal mesh: no thermal UA/HTC/Nu fit admission;
- sensor: 15 provisional diagnostic targets available after solve, with TP2 and
  TW10 blocked;
- solve_case: Slurm job `3293960` submitted/running, not harvested.

## Do Not Use As

Do not use this package as a final scorecard, a thermal closure fit, a complete
sensor validation package, or proof that forward-v1 is ready. Its purpose is to
show what can be scored now and exactly what remains blocked.
