---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/tested_model_form_sensor_errors.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/same_qoi_neighbor_triplet_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_qoi_projection_table.csv
tags: [model-form, d3, wall-shape, axial-mixing, same-qoi, thesis]
related:
  - .agent/journal/2026-07-22/mf-d3-wall-shape-axial-mixing-gate.md
  - imports/2026-07-22_mf_d3_wall_shape_axial_mixing_gate.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate/README.md
task: TODO-MF-D3-WALL-SHAPE-AXIAL-MIXING-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Tester / Writer / Reviewer
type: status
status: complete
---
# Status: D3 Wall-Shape / Axial-Mixing Gate

Task: `TODO-MF-D3-WALL-SHAPE-AXIAL-MIXING-GATE-2026-07-22`

## Objective

Determine whether the D3 wall-index transfer improvement can be explained by a
source-bounded wall/core exchange, axial-mixing, or sensor-projection mechanism.

## Outcome

Built `work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate/`.

Result:

- wall rows: `30`
- transfer wall rows: `20`
- candidate rows: `3`
- candidate-ready rows: `0`
- D3 transfer RMSE: `8.38846755024 K`
- D3 transfer local-shape RMSE after bias: `7.93285020379 K`
- D3 transfer RMSE reduction versus M3: `51.6919381995 %`
- same-QOI triplet-ready QOIs: `4`
- same-QOI UQ executed: `false`
- decision: `d3_wall_shape_signal_supported_diagnostic_only_same_qoi_triplets_ready_uq_not_executed`

D3 is a strong diagnostic wall-shape signal. It is not an admitted wall/core
exchange, axial-mixing, or sensor-projection closure.

## Changes Made

- Added `tools/analyze/build_mf_d3_wall_shape_axial_mixing_gate.py`.
- Added `tools/analyze/test_mf_d3_wall_shape_axial_mixing_gate.py`.
- Published `wall_index_residual_shape_decomposition.csv`.
- Published `wall_shape_case_summary.csv`.
- Published `s12_s13_evidence_crosswalk.csv`.
- Published `same_qoi_uq_requirement_table.csv`.
- Published `candidate_gate.csv`.
- Published `publication_claim_boundary.csv`.
- Published README, source manifest, guardrails, and summary.
- Updated `.agent/BOARD.md`.

## Validation

- `python3.11 tools/analyze/build_mf_d3_wall_shape_axial_mixing_gate.py` passed.
- `python3.11 tools/analyze/test_mf_d3_wall_shape_axial_mixing_gate.py` passed.

## Guardrails

- Native CFD/OpenFOAM outputs: no mutation.
- Registry/admission state: no mutation.
- Scheduler/solver/sampler/harvest/UQ: no launch.
- Fluid/external source trees: no mutation.
- Thesis current/LaTeX files: no mutation.
- No fitting, tuning, model selection, validation/holdout target use,
  source/property release, coefficient admission, runtime temperature input
  release, final score, or residual absorption into internal Nu.
