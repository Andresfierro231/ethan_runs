---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/selected_salt2_salt4_pm10q_after_3293924/status_table/selected_corrected_q_status_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/selected_salt2_salt4_pm10q_after_3293924/terminal_monitor_after_3293924/live_salt_sanity_monitor.csv
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
tags: [salt, pm10, terminal-admission, holdout, cfd-pp]
task: TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION
date: 2026-07-20
role: cfd-pp/Scheduler/Tester/Writer
type: work_product
status: complete
---
# Salt PM10 Terminal Admission Classification

This package classifies Salt2/Salt4 +/-10Q corrected-Q rows using the
`3293924` walltime stop and `3295438` completed harvest evidence. It performs
no model fitting and changes no registry or native CFD output.

## Summary

- PM10 rows classified: `4`.
- Future holdout scoring rows: `4`.
- Fit-admitted rows: `0`.
- Pressure/upcomer fit-admitted rows: `0`.
- Native output mutation: `none`.

## Files

- `scheduler_evidence.csv`
- `pm10_terminal_drift.csv`
- `pm10_heat_ledger_review.csv`
- `pm10_pressure_upcomer_review.csv`
- `pm10_split_decisions.csv`
- `pm10_terminal_admission_rows.csv`
- `source_manifest.csv`
- `summary.json`
