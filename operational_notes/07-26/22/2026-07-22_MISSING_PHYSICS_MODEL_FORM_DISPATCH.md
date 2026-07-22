---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_fluid_empirical_bias_models_publication_report/report.md
tags: [model-forms, missing-physics, entrance-development, signed-wall-flux, recirculating-upcomer]
related:
  - .agent/status/2026-07-22_TODO-MISSING-PHYSICS-MODEL-FORM-DISPATCH-2026-07-22.md
  - .agent/journal/2026-07-22/missing-physics-model-form-dispatch.md
  - imports/2026-07-22_missing_physics_model_form_dispatch.json
task: TODO-MISSING-PHYSICS-MODEL-FORM-DISPATCH-2026-07-22
date: 2026-07-22
role: Coordinator / Forward-pred / Thermal-modeling / Hydraulics / Writer / Reviewer
type: operational_note
status: complete
---
# Missing Physics Model-Form Dispatch

## Why This Exists

The scoreboard and diagnostic model-form studies show that the remaining
temperature residual is systematic, not random. The strongest diagnostic rows
improve error with low-dimensional corrections, but those corrections are not
yet physical closures. This note turns the most plausible missing physics into
board-ready studies.

## Suggested Missing Physics

The most likely missing physics is a combination of:

1. **thermal and hydraulic development after disturbances**
   - The loop is compact. Bends, junctions, heater/cooler boundaries, and
     material transitions can reset boundary layers before a branch becomes
     fully developed.

2. **signed wall-flux thermal development**
   - Cooler/HX and passive-loss regions remove heat from the fluid; heater and
     test-section source regions add heat. The local temperature profile and
     probe projection depend on the sign and axial placement of this exchange,
     not just total heat.

3. **source placement and wall-shape physics**
   - D3/D4 diagnostics indicate that wall-shape/axial-mixing and segment
     source placement can explain much of the residual shape. These need
     source-bounded physical forms before admission.

4. **recirculating upcomer physics**
   - The upcomer should not be forced into ordinary single-stream Nu/f_D/K.
     It needs either a guarded exclusion, a throughflow-plus-recirculation
     exchange cell, or a two-zone/stratified mixed-convection representation.

5. **bulk-to-probe projection**
   - D2 indicates TP/TW projection is promising. The 1D bulk state may be a
     poor proxy for local TP/TW probes when development and wall gradients are
     strong.

## How To Model It

The modeling should proceed in source-basis order, not score-first order.

MF07 should classify every segment by development state using geometry and
runtime-legal setup quantities: `Re`, `Pr`, `Gz`, `x/D` from last reset,
hydraulic entrance length, thermal entrance length, `Ri`, `Gr`, `Ra`, and
reverse-flow metrics. Output should be an eligibility table, not a correction
coefficient. A segment can only receive single-stream entrance/development
physics if the recirculation guard passes.

MF08 should use signed wall heat exchange. Model forms should distinguish:

- strong negative wall-flux development in the cooler/HX lane;
- weak negative wall-flux/passive cooling in the downcomer/passive-loss lane;
- positive wall-flux/source development in heater/test-section lanes;
- piecewise reset-memory where each source/sink or geometry feature resets the
  developing thermal profile.

The sign convention must be written explicitly in every artifact. Realized CFD
`wallHeatFlux` is not a runtime input. It may appear only as diagnostic
evidence when permitted by a row.

MF09 should isolate the recirculating upcomer. Try multiple alternatives:

- guard/exclude it from single-stream development and leave a residual;
- throughflow-plus-recirculation exchange cell with signed wall/source heat;
- two-zone stratified mixed-convection upcomer;
- source-side energy residual bridge, without relabeling source-side heat as
  wall heat flux.

MF10 should only run after MF07-MF09 publish source-basis gates. It should test
the predeclared variants on train/support rows only. It must not use
validation, holdout, or external-test rows for tuning or model selection.

MF11 should explain the empirical F2/F5 success. If the low-dimensional
coefficients align with entrance/development, signed wall flux, source
placement, wall-shape, upcomer exchange, or projection physics, the thesis can
say the empirical correction identified a physical residual family. If not,
F2/F5 remain diagnostic-only discrepancy models.

## Board Rows Added

- `TODO-MF07-ENTRANCE-DEVELOPMENT-AND-RESET-SOURCE-BASIS-2026-07-22`
- `TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22`
- `TODO-MF09-RECIRCULATING-UPCOMER-THERMAL-MODEL-ALTERNATIVES-2026-07-22`
- `TODO-MF10-ENTRANCE-WALLFLUX-TRAIN-ONLY-VARIANT-BAKEOFF-2026-07-22`
- `TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22`

## Documentation Requirements

Each row must document:

- process: exact files opened, calculations performed, and any commands run;
- assumptions: geometry, sign convention, source envelopes, reset locations,
  runtime inputs, and excluded regions;
- results: tables/figures, metrics if applicable, and failure modes;
- caveats: split use, source/property status, UQ status, and runtime legality;
- decision: one of the row-specific gates, such as `ready_for_train_only_smoke`,
  `diagnostic_only`, `needs_source_basis`, `blocked_missing_mesh_gci_source_basis`,
  `candidate_for_source_property_audit`, or `forbidden_as_fit`.

## Guardrails

No row should convert empirical residual compression into closure admission
without a source-bounded basis. No row should absorb unexplained thermal or
pressure residuals into internal Nu, friction, component K, or a hidden
multiplier. No row should tune on validation, holdout, or external-test rows.

The recirculating upcomer is explicitly not eligible for ordinary single-stream
Nu/f_D/K unless a future row proves the recirculation guard passes.
