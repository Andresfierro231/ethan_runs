---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/README.md
tags: [salt, pm10, terminal-admission, holdout, recirculation]
related:
  - .agent/status/2026-07-17_AGENT-493.md
  - .agent/journal/2026-07-17/salt-pm10-terminal-admission-readiness.md
task: AGENT-493
date: 2026-07-17
role: cfd-pp/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Salt PM10 Terminal Admission Readiness

This package defines `TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION` and captures
why terminal admission cannot be completed yet.

## Current State

- PM10 cases tracked: `4`.
- Jobs tracked: `2`.
- Cases ready for terminal admission now: `0`.
- Cases blocked by live/non-terminal jobs: `0`.
- Terminal admission performed here: `no`.

## PM5 Reference

PM5 postprocessing means the AGENT-406 scratch-copy matched-plane/wall-band
repair: reconstruct copied cases, sample upcomer planes and wall bands, validate
fields including `wallHeatFlux`, parse recirculation and dimensionless metrics,
and publish diagnostic admission tables. The old broken July 14 PM5 script was
not relaunched unchanged.

## Files

- `todo_definition.csv`
- `live_job_status.csv`
- `pm10_case_readiness.csv`
- `pm5_workflow_reference.csv`
- `terminal_admission_contract.csv`
- `postprocess_command_plan.md`
- `source_manifest.csv`
- `scheduler_query_diagnostics.json`
- `summary.json`
