---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/branch_local_thermal_admission.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models/segment_pressure_model_scorecard.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/segment_thermal_model_scorecard.csv
tags: [branch-specific, ordinary-pipe, admission, scorecard]
related:
  - .agent/status/2026-07-17_TODO-BRANCH-SPECIFIC-ORDINARY-PIPE-SCORECARD.md
  - .agent/journal/2026-07-17/branch-specific-ordinary-pipe-scorecard.md
task: TODO-BRANCH-SPECIFIC-ORDINARY-PIPE-SCORECARD
date: 2026-07-17
role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Branch-Specific Ordinary Pipe Scorecard

## Decision

No current branch is admitted for ordinary single-stream `Nu`, `f_D`, or physical `K` coefficient fitting. The package is complete as an admission mask: upcomer rows are handed to the hybrid lane, junctions remain named-loss diagnostics, and heater/cooler/test-section/downcomer rows keep their own gates.

## Results

- Branches reviewed: `7`.
- Branches included in ordinary aggregate fits: `0`.
- Ordinary coefficient fit-admitted rows: `0`.
- Exclusion handoff rows: `7`.
- Runtime audit pass rows: `4`.
