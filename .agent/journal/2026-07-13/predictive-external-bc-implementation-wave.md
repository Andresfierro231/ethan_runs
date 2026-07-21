---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/hx_primary_forward_scores.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/forward_v0_hydraulic_residuals.csv
tags: [forward-model, predictive-1d, external-boundary, radiation, hydraulic-guardrail]
related:
  - .agent/status/2026-07-13_AGENT-297.md
  - operational_notes/07-26/13/2026-07-13_PREDICTIVE_EXTERNAL_BC_IMPLEMENTATION_WAVE.md
task: AGENT-297
date: 2026-07-13
role: Coordinator/Implementer/Tester/Writer
type: journal
status: complete
---
# Predictive External BC Implementation Wave

## Observed

The prior wall-shell work made E1/E2 executable but did not close passive
external heat-loss residuals. The current validation split is usable:
`salt_2=train`, `salt_3=validation`, `salt_4=holdout`. The HX package has
split-aware outputs, but some protocol-status files still contain stale
missing-split language.

Two read-only parallel explorer agents were used:

- Fluid source map: identified `ScenarioConfig`, config loading,
  `ambient_loss_for_segment()`, `wall_and_insulation_resistances_per_length()`,
  existing fixed-loss replay, and segment-state reporting as the minimal Fluid
  edit points.
- Scorecard input map: confirmed the split-aware HX, validation split, forward
  v0, and hydraulic gate CSVs are sufficient for table-level scoring without a
  new Fluid run.

## Implemented

Added:

- `tools/analyze/build_predictive_external_bc_implementation_wave.py`
- `tools/analyze/test_predictive_external_bc_implementation_wave.py`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/**`
- `imports/2026-07-13_predictive_external_bc_implementation_wave.json`
- this status/journal/operational handoff.
- additive cross-link in `operational_notes/maps/forward-predictive-model.md`.

Generated package row counts:

- external boundary rows: 24
- boundary score rows: 24
- HX score rows: 6
- hydraulic summary rows: 2
- decision rows: 4

## Interpretation

The CFD external-boundary dictionary is ready for a Fluid implementation lane,
but not yet executed in Fluid because external source was read-only in this
workspace. The correct Fluid implementation is a dynamic external-boundary
table, not a fixed `Q_ambient_W` replay.

Radiation handling is fixed for downstream agents:

- setup-level external-BC parity includes emissivity/Tsur radiation;
- realized CFD `wallHeatFlux` replay does not add a separate radiation term.

Hydraulic guardrails remain the limiting issue. `F0_current_fluid_sources`
overpredicts mdot by mean `0.008081667 kg/s`; `F1_heater_only` overpredicts by
mean `0.0054775 kg/s`. Thermal or HX improvements cannot be reported as
end-to-end predictive success until that bias is addressed.

## Validation

- `python3.11 -m py_compile tools/analyze/build_predictive_external_bc_implementation_wave.py tools/analyze/test_predictive_external_bc_implementation_wave.py`
- `python3.11 tools/analyze/test_predictive_external_bc_implementation_wave.py`
- `python3.11 tools/analyze/build_predictive_external_bc_implementation_wave.py`
- `python3 tools/docs/build_repo_index.py`
- `python3 tools/docs/build_repo_index.py --check`

All passed. No OpenFOAM solve, Fluid solve, scheduler submission, native-output
mutation, or external Fluid source edit was performed.

## Next

1. Claim a writable Fluid row and implement `ambient_loss_model =
   external_boundary_table` using `fluid_external_boundary_patch_plan.md`.
2. Run narrow Fluid tests for radiation/Tsur/emissivity and no-double-counting.
3. Re-score Salt2/Salt3/Salt4 under the declared split.
4. Keep thermal mesh/admission and hydraulic correction lanes separate.
