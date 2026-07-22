---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/adjacent_pressure_ladder.csv
  - work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/adjacent_pressure_ladder.csv
  - work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan/current_evidence_recirculation_classification.csv
  - work_products/2026-07/2026-07-15/2026-07-15_branch_specific_ordinary_pipe_scorecard/branch_specific_fit_mask.csv
tags: [pressure-ladder, hydraulics, recirculation-mask, branch-orientation]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch/README.md
task: AGENT-449
date: 2026-07-16
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# Pressure Ladder Harvest Admission Table

## Purpose

This package integrates the completed July 15 pressure-ladder harvests into the
branch orientation, straight-loss subtraction, and recirculation-mask admission
screen requested for the next hydraulic step. It consumes existing harvested
CSV outputs only. No duplicate pressure-ladder, closure-QOI, or OpenFOAM jobs
were submitted.

## Outputs

- `branch_orientation_straight_loss_recirc_admission.csv`: one row per
  `case_key` plus branch, with adjacent `p_rgh` orientation screening,
  straight-loss subtraction readiness, pressure-definition conflicts, and
  recirculation-mask status.
- `adjacent_pair_recirc_screen.csv`: one row per adjacent station pair from the
  harvested ladders with reverse-area mask classification.
- `case_pressure_ladder_admission_summary.csv`: case-level rollup.
- `source_manifest.csv`: exact source packages and job IDs.

## Result

Harvested ladder inputs are available and parsed:

- AGENT-445 job `3297860`: 72 adjacent rows.
- AGENT-447 job `3297863`: 192 adjacent rows.
- Integrated branch rows: 66.
- True `f_D` or component `K` fit-admitted branch rows: 0.

Every branch remains diagnostic for coefficient fitting. The most common
blocking reasons are recirculation masks, unresolved or screen-only orientation,
static-`p` versus `p_rgh` pressure-definition conflicts, missing geometry
distance normalization, missing mesh/GCI, and absent component isolation. The
upcomer-related branches (`left_lower_leg`, `test_section_span`, and
`left_upper_leg`) stay in the hybrid/onset lane, not ordinary single-stream
`Nu`, `f_D`, or `K` fitting.

## Admission Contract

Use these tables to decide what to analyze next, not as final coefficients.
Before any localized `K` or distributed `f_D` fit, a future package must admit
pressure definition, tap orientation, straight-loss subtraction, low
recirculation (`RAF < 0.01` for true single-stream fits), mesh/GCI, and
time-window/source provenance together.
