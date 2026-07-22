---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_d2_holdout_validation_disposition/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_d2_holdout_validation_disposition/d2_metric_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/candidate_bulk_to_tp_formulas.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/split_claim_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_model_form_scoreboard_training_roster/trainability_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/field_release_contract.csv
tags: [d2, bulk-to-tp, sensor-projection, holdout, external-test, diagnostic-only]
related:
  - .agent/status/2026-07-22_TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22.md
  - .agent/journal/2026-07-22/d2-source-bounded-projection-holdout-external-score-gate.md
  - imports/2026-07-22_d2_source_bounded_projection_holdout_external_score_gate.json
task: TODO-D2-SOURCE-BOUNDED-PROJECTION-HOLDOUT-EXTERNAL-SCORE-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Sensor-map / Forward-pred / Writer / Reviewer / Tester
type: work_product
status: complete
---
# D2 Source-Bounded Projection Holdout/External Score Gate

Decision: `fail_closed_d2_not_protected_scoreable_source_bounded_successors_not_frozen`.

D2 is useful evidence that the temperature discrepancy has a bulk-to-TP /
sensor-kind projection component, but D2 itself is still an empirical diagnostic
offset model. It is not a frozen runtime-legal candidate and should not be
tested on validation, holdout, or external-test data as-is.

## Models In Play

The scoreable successor path is not "D2 offsets on protected data." The models
to try are source-bounded projection forms:

1. `MF12a_signed_graetz_probe_offset`: a local TP correction from bulk using
   source sign, Graetz/reset distance, boundary condition class, and sensor map.
2. `MF12b_piecewise_signed_source_integral`: an upstream thermal-memory model
   that integrates legal setup heat sources/sinks through a reset kernel.
3. `MF12c_wall_profile_projection`: a wall/core profile projection from bulk to
   a local probe using a source-bounded wall/profile state.
4. `MF15_wall_core_exchange_operator` and
   `M5_MF04_throughflow_recirculation_exchange_cell`: downstream wall-core and
   recirculating-exchange models that can own remaining thermal structure after
   TP projection.

`D2_empirical_offset` remains a hypothesis generator: it says the shape and
magnitude of the error are compatible with sensor projection / thermal
development, not that the empirical offset is predictive.

## Holdout/External Answer

No protected D2 scoring was run in this package. Current gates say:

- validation scoring allowed now: `false`;
- holdout scoring allowed now: `false`;
- external-test scoring allowed now: `false`;
- frozen candidate manifest exists: `false`;
- source/property/cp release complete: `false`;
- same-QOI projection UQ release complete: `false`;
- runtime use of validation/holdout/external temperatures: `false`.

Protected scoring should wait until one source-bounded candidate is frozen from
train/support only. Then validation, holdout, and external-test rows can be
scored exactly once with no coefficient changes after seeing them.

## Boundary/Development-Layer Interpretation

The physical story to describe in the thesis is:

- The 1D segment state is a bulk mixed-cup temperature. A thermocouple-like TP
  value is a local sampled temperature and can differ from the segment bulk when
  the thermal profile is developing.
- Heater, cooler, passive loss, jacket, and wall conduction terms create signed
  boundary forcing. Their effect is not instantaneously mixed at every probe.
- Reset events such as bends, junctions, branch exchange, or boundary-condition
  changes can restart hydraulic and thermal development. A Graetz/reset
  coordinate is therefore a natural state variable for bulk-to-TP projection.
- Near-wall sensors and wall-proximate probes are sensitive to wall/core
  contrast. This belongs in a projection or wall-core lane, not as hidden
  residual in internal `Nu`.
- After the bulk-to-TP projection is accounted for, remaining TW residual must
  stay in wall conduction, wall/core exchange, passive/external boundary,
  source/sink, storage, or residual lanes.

## Output Contract

This package publishes:

- `projection_model_family_table.csv`: model-family definitions and blockers.
- `protected_score_gate.csv`: holdout/external score permission by candidate.
- `freeze_prerequisite_checklist.csv`: exact gates before protected scoring.
- `d2_holdout_external_score_decision.csv`: direct answer to the D2 score
  request.
- `thesis_description_scaffold.md`: thesis-ready methodology scaffold.
- `source_manifest.csv`, `no_mutation_guardrails.csv`, and `summary.json`.

No CFD/native output, registry, scheduler, Fluid source, external repository, or
thesis body file was mutated.
