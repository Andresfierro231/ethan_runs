---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/hybrid_1d_model_contract.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_holdout_metrics.csv
  - work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard/upcomer_onset_classification.csv
tags: [upcomer, recirculation, hybrid-model, admission]
related:
  - .agent/status/2026-07-17_TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL.md
  - .agent/journal/2026-07-17/upcomer-pipe-cell-hybrid-model.md
task: TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL
date: 2026-07-17
role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Upcomer Pipe-Cell Hybrid Model

## Decision

The upcomer is treated as a throughflow pipe branch plus recirculating convection-cell exchange. Current evidence admits the hybrid lane as a diagnostic contract only. Ordinary single-stream `Nu`, `f_D`, `K`, and F6 labels remain blocked for current recirculating rows.

## Results

- Hybrid candidate lanes: `4`.
- Recirculation feature rows: `6`.
- Ordinary upcomer coefficient fit-admitted rows: `0`.
- Hybrid predictive fit-admitted rows: `0`.
- Onset/calibration gaps: `3`.
- Runtime audit pass rows: `4`.
