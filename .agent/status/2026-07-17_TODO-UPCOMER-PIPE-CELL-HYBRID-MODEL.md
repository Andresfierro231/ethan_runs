---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/summary.json
tags: [status, upcomer, hybrid-model]
related:
  - .agent/journal/2026-07-17/upcomer-pipe-cell-hybrid-model.md
  - imports/2026-07-17_upcomer_pipe_cell_hybrid_model.json
task: TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL
date: 2026-07-17
role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL Status

## Observed Facts

- PM5 and recirculation evidence show material reverse-flow fractions in current upcomer rows.
- Current rows are diagnostic/hybrid evidence, not ordinary pipe closure data.
- Onset anchors and split-scored hybrid penalty calibration are still missing.

## Changes Made

- Wrote `work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/` with hybrid candidate contract, feature scorecard, admission decisions, onset gaps, runtime audit, README, and summary.
- Added focused builder tests.

## Validation

- `python3 -m unittest tools.analyze.test_upcomer_pipe_cell_hybrid_model`
- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.

## Blockers

- No blocker remains for documenting the hybrid lane contract.
- Predictive upcomer closure remains blocked by ordinary/transition anchors, mesh/time uncertainty, and train/validation/holdout scoring of a frozen hybrid penalty.
- Generated docs index refresh was skipped because active board rows own generated index files.
