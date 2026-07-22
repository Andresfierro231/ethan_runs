---
provenance:
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/branch_source_envelope.csv
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/reset_distance_map.csv
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-21/2026-07-21_litrev_gated_single_stream_developing_branch/single_stream_developing_branch_gate.csv
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/tested_model_form_sensor_errors.csv
tags: [mf07, entrance-development, reset, graetz, bulk-to-tp]
related:
  - .agent/status/2026-07-22_TODO-MF07-ENTRANCE-DEVELOPMENT-AND-RESET-SOURCE-BASIS-2026-07-22.md
  - operational_notes/07-26/22/2026-07-22_MF07_ENTRANCE_DEVELOPMENT_AND_RESET_SOURCE_BASIS.md
task: TODO-MF07-ENTRANCE-DEVELOPMENT-AND-RESET-SOURCE-BASIS-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# MF07 Entrance/Development and Reset Source Basis

Decision: `diagnostic_only`.

This package continues the D2 TP-first path by joining TP signed residuals to
reset distance, Graetz/development coordinates, source-sign envelopes, and S13
wall/core exchange evidence. It is evidence-only: no coefficient, no corrected
prediction, no final score, and no admission is produced.

Main result:

- Segment classification rows: `33`.
- TP residual/reset/Graetz join rows: `10`.
- Predeclared variants: `3`.
- S13 bridge rows: `7`.
- Max S13 wall/core contrast over D2 train TP offset:
  `0.011299990251356482`.
- Train-only smoke ready: `False`.

Interpretation:

- Hydraulic reset/development is useful context but cannot by itself explain a
  bulk-to-TP temperature offset without a coupled pressure/thermal closure.
- Thermal Graetz/development has the right kind of source basis for heated
  spans, but thermal reset labels, same-QOI TP projection UQ, and a released
  formula are still missing.
- S13 exchange evidence is useful as a TP bridge, but the wall/core contrast is
  too small to explain the full D2 TP offset by itself and remains diagnostic
  until mesh/GCI, source/property, and production-use gates pass.

Primary files:

- `segment_classification_table.csv`
- `tp_residual_reset_graetz_join.csv`
- `variant_direction_of_effect.csv`
- `bulk_to_tp_existence_proof_gate.csv`
- `s13_wall_core_tp_bridge_matrix.csv`
- `next_analysis_plan.csv`
- `formula_provenance_table.csv`
- `missing_input_table.csv`
- `tw_after_tp_next_gate.csv`
- `candidate_gate.csv`
- `runtime_legality_matrix.csv`
