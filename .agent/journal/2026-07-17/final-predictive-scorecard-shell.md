---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/summary.json
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/summary.json
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
tags: [journal, final-scorecard, corrected-split, holdout-policy]
related:
  - .agent/status/2026-07-17_AGENT-509.md
  - imports/2026-07-17_final_predictive_scorecard_shell.json
task: AGENT-509
date: 2026-07-17
role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# Final Predictive Scorecard Shell

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/{README.md,split_legal_case_table.csv,candidate_freeze_manifest.csv,blocked_future_rows.csv,summary.json}`
- `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/{summary.json,val_salt2_prediction_join_contract.csv,val_salt2_external_score_targets.csv,val_salt2_external_residual_scorecard.csv,pm10_holdout_admission_watch.csv}`
- `work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/pm10_case_readiness.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/summary.json`

## Files Changed

- Added `tools/analyze/build_final_predictive_scorecard_shell.py`
- Added `tools/analyze/test_final_predictive_scorecard_shell.py`
- Generated `work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/**`
- Added `.agent/status/2026-07-17_AGENT-509.md`
- Added this journal entry
- Added `imports/2026-07-17_final_predictive_scorecard_shell.json`
- Updated `.agent/BOARD.md` own AGENT-509 row status

## Observed Evidence

AGENT-499 provides the corrected split: Salt1-4 nominal are the only training
rows, Salt2 +/-5Q and `val_salt2` are blind score-only rows, and +/-10Q/new CFD
are future rows. It also records no admitted final candidate and no corrected
Salt1-4 freeze.

AGENT-500 provides `val_salt2` external target readiness: 61 external targets,
including 30 pressure targets, 14 thermal targets, and 17 sensor targets; it
also records zero joined frozen predictions and keeps TP2/TW10 excluded from
the aggregate policy.

Salt2 +/-5Q has PM5 diagnostic rows for both `salt2_lo5q` and `salt2_hi5q`.
Those rows are holdout diagnostics only and are explicitly not fit/model
selection evidence.

PM10 rows remain future rows. The cited readiness/watch tables still record
live/pending job state for the four +/-10Q cases. The Salt3 Q x insulation
matrix remains proposed/not run.

AGENT-498 leaves wall/test-section distribution candidates not admitted. This
matters because the final shell can prepare the row contract, but a real frozen
prediction artifact still requires an admitted model candidate.

## Implementation Notes

The builder creates a scorecard shell, not a scorecard result. It emits:

- `case_partition_contract.csv`
- `model_freeze_contract.csv`
- `metric_contract.csv`
- `prediction_join_shell.csv`
- `holdout_release_gates.csv`
- `admission_gate_shell.csv`
- `assumption_ledger.csv`
- `runtime_input_audit.csv`
- `scorecard_summary.csv`
- `source_manifest.csv`
- `summary.json`
- `README.md`

The main assumption is that a future task will produce a frozen prediction
artifact with `prediction_model_id` and the metric-specific fields listed in
`metric_contract.csv`. Until then, all prediction rows are placeholders.

## Commands Run

- `python3 -m py_compile tools/analyze/build_final_predictive_scorecard_shell.py tools/analyze/test_final_predictive_scorecard_shell.py`
- `python3 -m unittest tools.analyze.test_final_predictive_scorecard_shell`
- `python3 -m json.tool work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/summary.json`

## Results

Validation passed. The generated summary reports:

- training cases: `4`
- current blind holdout/external cases: `3`
- future test cases: `5`
- excluded support cases: `4`
- metric contract rows: `7`
- prediction placeholder rows: `79`
- holdout release-gate rows: `8`
- runtime audit failures: `0`
- score status: `shell_ready_no_final_scores`

## Incomplete Lines Of Investigation

No final scores are computed because there is no admitted final freeze. The
active AGENT-507 and AGENT-508 scopes were treated as read-only and were not
consumed as final evidence. This package deliberately does not resolve model
admission or val_salt2 prediction joins.

## Next Actions

1. Complete the wall/test-section/admission closeout and any admitted model
   candidate path.
2. Build a final frozen prediction artifact using Salt1-4 nominal only.
3. Join that artifact into `prediction_join_shell.csv`.
4. Release Salt2 +/-5Q and `val_salt2` for scoring only after the freeze exists.
5. Release +/-10Q/new CFD rows only after terminal/run admission and the freeze.
