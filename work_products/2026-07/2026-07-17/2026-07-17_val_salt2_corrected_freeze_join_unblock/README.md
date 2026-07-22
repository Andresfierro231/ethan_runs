---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/val_salt2_external_score_targets.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/val_salt2_prediction_join_contract.csv
  - work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/summary.json
tags: [val-salt2, corrected-freeze, external-score, prediction-join, guardrails]
related:
  - .agent/status/2026-07-17_AGENT-508.md
  - .agent/journal/2026-07-17/val-salt2-corrected-freeze-join-unblock.md
task: AGENT-508
date: 2026-07-17
role: Forward-pred/cfd-pp/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 Corrected-Freeze Join Unblock

This package implements the next unblocking step for `val_salt2`: audit whether
a corrected-split frozen prediction source exists, then join predictions to the
AGENT-500 target contract when a valid source is supplied.

## Result

- Freeze status: `freeze_blocked_no_wall_candidate_admitted`.
- Target rows reviewed: `61`.
- Prediction rows joined/scored: `0`.
- Policy-excluded rows: `2`.
- Rows still blocked or missing prediction: `59`.
- Score-summary lanes with joined predictions: `0`.

## Interpretation

The current repository state still does not provide a corrected-split final
freeze suitable for blind `val_salt2` scoring. AGENT-498 completed coupled wall
distribution scoring but admitted no wall/test-section candidate, and AGENT-499
therefore reports zero final admitted predictive candidates.

The builder is ready to rerun with `--prediction-csv` once a corrected-split
frozen prediction table exists. Until then, `val_salt2` remains target-ready but
not residual-scored.

## Continue Here

Open `corrected_freeze_source_audit.csv` and
`val_salt2_external_residual_scorecard.csv`. The next productive implementation
is a corrected-split freeze runner trained on Salt1-4 nominal only. Do not use
`val_salt2` errors to tune that runner.
