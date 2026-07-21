---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/next_agent_task_matrix.csv
tags: [board-dispatch, litrev-synthesis, model-forms, one-d-model, cfd-postprocessing]
related:
  - .agent/status/2026-07-21_TODO-LITREV-MODEL-FORM-BOARD-DISPATCH-2026-07-21.md
  - imports/2026-07-21_litrev_model_form_board_dispatch.json
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/README.md
task: TODO-LITREV-MODEL-FORM-BOARD-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer
type: journal
status: complete
---
# LitRev Model-Form Board Dispatch

Task: TODO-LITREV-MODEL-FORM-BOARD-DISPATCH-2026-07-21

## Attempted

Assigned the model forms and evidence-preparation tasks identified in the
new-LitRev extraction package onto the board as open, future-claimable TODO rows.
The board update was intentionally limited to additive rows under
`## Planned / Unclaimed`.

## Observed

The extraction package contains six model forms and seven immediate next-agent
lanes. Existing board rows already cover some older or completed versions of
ordinary pipe scorecards, upcomer hybrid contracts, and broad model-form
bakeoffs, but the new LitRev package adds more precise requirements around
pressure basis, velocity basis, recovery, recirculation diagnostics, source
envelope, and heat-loss separation.

The current board still contains completed rows in `## Active`; this task did
not clean them up because cleanup was not part of the user request and would be
a separate coordinator action.

## Inferred

The highest-priority immediate rows are pressure/fitting/CFD-contract lanes:
fitting inventory/source envelope, pressure-corner basis/recovery, and CFD
postprocessing schema gap. These prepare evidence without fitting. The
model-form lanes then split into gated single-stream developing branch,
throughflow-plus-recirculation exchange cell, and signed-flow feasibility. The
transient and ROM forms are correctly parked because their trigger evidence is
not current.

## Caveats

These board rows do not implement models. They only define future scopes,
inputs, outputs, acceptance signals, and guardrails. Current F6, two-tap,
component-K, internal-Nu, and recirculation-cell admissions remain unchanged.

## Next Useful Actions

Have future agents claim one row at a time, starting with:
`TODO-LITREV-FITTING-INVENTORY-SOURCE-ENVELOPE`,
`TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY`, or
`TODO-LITREV-CFD-POSTPROCESSING-SCHEMA-GAP`.
