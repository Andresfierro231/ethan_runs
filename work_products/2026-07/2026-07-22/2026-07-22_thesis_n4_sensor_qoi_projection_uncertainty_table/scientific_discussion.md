---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_sensor_map_contract/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s6_frozen_candidate_scorecard/summary.json
tags: [thesis, synthesis, publication-evidence, n4]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n1_frozen_runtime_legal_candidate_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n3_thermal_residual_owner_train_ablation/README.md
task: TODO-THESIS-N4-SENSOR-QOI-PROJECTION-UNCERTAINTY-TABLE-2026-07-21
date: 2026-07-22
role: Sensor-map / Uncertainty / Tester / Writer
type: work_product
status: complete
---

# Thesis N4 Sensor QOI Projection Uncertainty Table Scientific Discussion

## Observed Evidence

The sensor packages review 17 TP/TW sensors: one mapped target, fifteen bounded
targets, and one excluded target. Every row preserves
`runtime_temperature_allowed=false`, `fit_allowed=false`, and
`model_selection_allowed=false`.

## Interpretation

Sensor uncertainty is a QOI projection issue. It affects how score tables and
captions should be written, but it must not leak target temperatures into model
runtime, fitting, or model selection.
