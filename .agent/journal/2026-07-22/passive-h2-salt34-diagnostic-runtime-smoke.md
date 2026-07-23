---
task: TODO-PASSIVE-H2-SALT34-DIAGNOSTIC-RUNTIME-SMOKE-2026-07-22
provenance:
  generated_by: tools/analyze/build_passive_h2_salt34_diagnostic_runtime_smoke.py
  task_id: TODO-PASSIVE-H2-SALT34-DIAGNOSTIC-RUNTIME-SMOKE-2026-07-22
tags: [journal, PASSIVE-H2, runtime-smoke]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt34_diagnostic_runtime_smoke/case_runtime_smoke_summary.csv
---
# PASSIVE-H2 Salt3/Salt4 Diagnostic Runtime Smoke

## Attempted

Ran Salt3 and Salt4 through the existing Fluid PASSIVE-H2 smoke runner under
`srun` using task-local diagnostic operator rows and local output roots.

## Observed

Completed cases `2/2`; accepted root sets
`2/2`; nonzero radiation movement cases
`2/2`.

## Inferred

This adds diagnostic runtime support for H2 beyond Salt2, but does not unlock
admission. Next useful work is exact same-QOI runtime-neighbor UQ, then
candidate-specific source/property gate rerun.
