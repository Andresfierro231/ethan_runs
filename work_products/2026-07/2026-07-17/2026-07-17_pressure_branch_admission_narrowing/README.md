---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models/segment_pressure_model_scorecard.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/branch_orientation_straight_loss_recirc_admission.csv
  - work_products/2026-07/2026-07-17/2026-07-17_branch_specific_ordinary_pipe_scorecard/ordinary_pipe_branch_mask.csv
tags: [pressure, branch-admission, scorecard, blocker]
related:
  - .agent/status/2026-07-17_TODO-PRESSURE-BRANCH-ADMISSION-NARROWING.md
  - .agent/journal/2026-07-17/pressure-branch-admission-narrowing.md
task: TODO-PRESSURE-BRANCH-ADMISSION-NARROWING
date: 2026-07-17
role: Hydraulics/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Pressure Branch Admission Narrowing

## Decision

No segment-local pressure coefficient is admitted by this narrowing pass. The package completes the blocker narrowing by branch and gate; `lower_upper_legs` is the least-risk next technical target but still blocked.

## Results

- Branch rows: `7`.
- Fit-admitted pressure rows: `0`.
- Least-risk candidates: `1`.
- Missing-evidence rows: `33`.
- Runtime audit pass rows: `4`.
