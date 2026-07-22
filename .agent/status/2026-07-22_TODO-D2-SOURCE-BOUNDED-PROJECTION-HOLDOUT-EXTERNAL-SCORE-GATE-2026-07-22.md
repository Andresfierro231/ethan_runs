---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/protected_score_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/projection_model_family_table.csv
tags: [d2, holdout, external-test, bulk-to-tp, score-gate]
related:
  - .agent/journal/2026-07-22/d2-source-bounded-projection-holdout-external-score-gate.md
  - imports/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate.json
task: TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Sensor-map / Forward-pred / Writer / Reviewer / Tester
type: status
status: complete
---
# Status: D2 Source-Bounded Projection Holdout/External Score Gate

Decision: `fail_closed_d2_not_protected_scoreable_source_bounded_successors_not_frozen`.

## Objective

Answer whether D2 can be tested on holdout and external-test data now, while
documenting the actual bulk-to-TP / sensor-kind projection models in
boundary/development-layer terms.

## Outcome

D2 should not be scored on protected holdout or external-test data as-is. It is
a useful empirical diagnostic showing that bulk-to-TP / sensor-kind projection
matters, but it is not a runtime-legal frozen candidate.

Source-bounded successor families were documented:

- `MF12a_signed_graetz_probe_offset`;
- `MF12b_piecewise_signed_source_integral`;
- `MF12c_wall_profile_projection`;
- `MF15_wall_core_exchange_operator`;
- `M5_MF04_throughflow_recirculation_exchange_cell`.

All protected-score gates remain closed because no frozen candidate exists,
source/property/cp release is incomplete, same-QOI projection UQ is not released,
and wall/core/S13 exchange gates remain blocked.

## Changes Made

- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/projection_model_family_table.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/protected_score_gate.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/freeze_prerequisite_checklist.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/d2_holdout_external_score_decision.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/thesis_description_scaffold.md`
- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/source_manifest.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/no_mutation_guardrails.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate/summary.json`
- `.agent/journal/2026-07-22/d2-source-bounded-projection-holdout-external-score-gate.md`
- `imports/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate.json`
- `.agent/BOARD.md`

## Validation

- CSV/JSON parse checks passed for the new package.
- `python3.11 tools/agent/finish_task.py --task-id TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22` passed.

## Guardrails

No validation, holdout, or external-test scoring was run. No fitting, model
selection, source/property release, candidate freeze, coefficient admission,
final-score claim, scheduler action, native-output mutation, registry mutation,
Fluid/external edit, thesis body edit, or residual absorption into internal
`Nu` occurred.

## Next Useful Actions

1. Complete source/property/cp release for one MF12 candidate using train/support
   rows only.
2. Complete same-QOI TP projection UQ for that predeclared candidate.
3. Freeze exactly one runtime-legal candidate manifest before any protected
   validation, holdout, or external-test scoring.
