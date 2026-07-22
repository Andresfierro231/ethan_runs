---
provenance:
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/tested_model_form_scoreboard.csv
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_qoi_projection_table.csv
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-21/2026-07-21_litrev_gated_single_stream_developing_branch/single_stream_developing_branch_gate.csv
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/reset_distance_map.csv
tags: [d2, tp, tw, qoi-projection, thermal-development]
related:
  - .agent/status/2026-07-22_TODO-MF-D2-TP-TW-QOI-PROJECTION-GATE-2026-07-22.md
  - operational_notes/07-26/22/2026-07-22_MF_D2_TP_TW_QOI_PROJECTION_GATE.md
task: TODO-MF-D2-TP-TW-QOI-PROJECTION-GATE-2026-07-22
date: 2026-07-22
role: Sensor-map / Uncertainty / Thermal-modeling / Tester / Writer / Reviewer
type: work_product
status: complete
---
# MF-D2 TP/TW QOI Projection Gate

Decision: `thermal_development_path_promising_diagnostic_only_no_correction_release`.

This package audits whether the D2 TP/TW diagnostic improvement should be read
as a QOI projection / bulk-to-TP thermal-development signal. It does not admit a
correction.

Main result:

- D2 improves transfer TP RMSE from M3 `13.5673279702 K` to `4.38159298515 K`.
- D2 improves transfer TW RMSE from M3 `18.980361511 K` to `12.5130610954 K`.
- The stronger TP improvement supports the analysis sequence: bulk/TP
  projection first, then TW wall/boundary response.
- A released bulk-to-TP thermal-development correction does not yet exist.

Primary files:

- `d2_score_improvement_summary.csv`
- `tp_tw_residual_separation.csv`
- `bulk_to_tp_correction_existence_audit.csv`
- `tp_projection_thermal_development_evidence.csv`
- `runtime_legality_matrix.csv`
- `next_analysis_plan.csv`
- `publication_claim_boundary.csv`
- `figures/svg/d2_tp_tw_projection_transfer_rmse.svg`

Guardrails: no fitting, no source/property release, no closure admission, no
final score, no scheduler or solver action, no native-output mutation, no Fluid
edit, and no residual absorption into internal Nu.
