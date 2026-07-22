---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_pm10_upcomer_anchor_admission/pm10_recirculation_feature_matrix.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pm10_upcomer_anchor_admission/pm10_recirculation_anchor_admission.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/hybrid_1d_model_contract.csv
tags: [pm10, recirculation, upcomer, residual-scorecard, hybrid-model]
date: 2026-07-20
type: work_product
status: active
---
# PM10 Recirculation Hybrid Residual Scorecard

This package makes the repaired PM10 matched-plane extraction usable as
recirculation-aware evidence. PM10 remains excluded from ordinary pipe `Nu`,
`f_D`, component-`K`, model-selection, and runtime-input use.

## Decision

The current PM10 rows are in the `recirculating_upcomer_effective` lane. They
can support recirculation diagnostics and conditional hybrid-model review, but
fit/model-selection promotion still requires same-window residual targets,
split scoring, and mesh/time uncertainty.

## Outputs

- `pm10_recirc_feature_summary.csv`: 4 case-level feature rows from 12 plane rows.
- `pm10_recirc_residual_join.csv`: residual target join status for each PM10 row.
- `pm10_recirc_model_form_scorecard.csv`: recirculation-aware model-form dry/available scores.
- `pm10_recirc_blocker_queue.csv`: concrete unblocks for residual targets, UQ, transition anchors, and runtime policy.
- `source_manifest.csv`: source paths and availability.
