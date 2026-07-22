---
provenance:
  - .agent/BOARD.md
  - operational_notes/07-26/22/2026-07-22_THESIS_TOMORROW_CONTEXT_PROGRESS_HANDOFF.md
  - operational_notes/07-26/22/2026-07-22_S13_UPCOMER_EXCHANGE_TOMORROW_CONTEXT_HANDOFF.md
  - operational_notes/07-26/22/2026-07-22_THESIS_N1_N4_SYNTHESIS_TOMORROW_HANDOFF.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_five_best_thesis_support_analyses/README.md
  - .agent/BLOCKERS.md
tags: [coordination, board-cleanup, thesis, predictive-1d, work-avenues]
related:
  - .agent/status/2026-07-22_TODO-BOARD-CLEANUP-AND-AVENUE-GAP-DISPATCH-2026-07-22.md
  - .agent/journal/2026-07-22/board-cleanup-and-avenue-gap-dispatch.md
  - imports/2026-07-22_board_cleanup_and_avenue_gap_dispatch.json
task: TODO-BOARD-CLEANUP-AND-AVENUE-GAP-DISPATCH-2026-07-22
date: 2026-07-22
role: Coordinator/Cleaner/Writer/Reviewer
type: operational_note
status: complete
---
# Board Cleanup and Avenue Gap Dispatch

Task: `TODO-BOARD-CLEANUP-AND-AVENUE-GAP-DISPATCH-2026-07-22`

## Board Cleanup

The `## Active` section was cleaned first. Thirteen rows that already self-reported completion were archived under `Archived Complete - 2026-07-22 Coordinator Stale Lock Cleanup` after `finish_task.py --json` passed for each. The S13 same-QOI neighbor row completed during this coordinator pass, passed `finish_task.py --json`, and was archived under `Archived Complete - 2026-07-22 S13 Neighbor UQ Immediate Closeout`. This coordinator row was also archived at closeout. Final Active had `11` rows and `0` self-complete stale locks.

Important current Active rows to avoid overlapping:

- `TODO-S10-S14-PRESSURE-F6-CAND001-RETRY-AND-UQ-GATE-2026-07-21`: already represents the pressure/F6 retry/UQ gate lane.
- `TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-PRODUCTION-HARVEST-UQ-2026-07-21`: trigger-gated production harvest lane; do not launch before S13 UQ gates pass.
- `AGENT-519`: read-only scheduler monitor; do not submit/cancel/requeue from unrelated rows.

## What Is Already Pursued

- S13 direct Qwall and pressure extraction exists, and the neighbor-window same-QOI row closed fail-closed: `12` target-window rows, `0` target-minus, `0` target-plus, and `0/4` same-QOI neighbor-UQ-ready labels.
- S13 production harvest is already on the board but remains trigger-gated.
- Pressure/F6 CAND001 retry/UQ gate is already on the board.
- Final freeze, S11 source/property refresh, and S15 score release are already on the board but remain trigger-gated.
- Thesis figure, enrichment, and post-freeze/pressure/wall closure writing rows already exist at broad level.

## Main Gaps

1. **Chapter 4 thesis bridge is not actively owned.**
   Chapters 5 and 6 have LaTeX sync work, but Chapter 4 is the natural place to explain CFD-to-1D reduction, evidence classes, split discipline, and runtime-leakage prevention.

2. **S13 needs mesh/GCI after neighbor-window UQ failed closed.**
   The completed S13 row found no target-minus/target-plus same-QOI neighbor support, so the next separate gate must decide whether direct `Q_wall_W` and exchange QOIs have any defensible mesh/GCI or time uncertainty basis before production harvest.

3. **AMX1 is a promising physical model but needs an external Fluid implementation packet.**
   Current TSWFC2 and UMX1 rows did not unlock the wall/test-section blocker. The AMX1 dry contract points to axial mixing/stratification, but no exact external Fluid handoff packet is active.

4. **Source/property release is still too candidate-coupled.**
   S11/S15 are trigger-gated for exactly one candidate, but a row-level nominal-train release preflight could expose missing labels and source-envelope blockers before a candidate appears.

5. **Thesis can gain value from figures/tables without new science.**
   The N1-N4, model-form scoreboard, blocked scorecard, and negative pressure/S13 evidence are ready for insert-grade panels that keep final score values at zero.

## Board Rows Added

- `TODO-THESIS-LATEX-CH4-REDUCTION-SPLIT-SYNC-2026-07-22`
- `TODO-S13-UPCOMER-EXCHANGE-QWALL-MESH-GCI-UQ-GATE-2026-07-22`
- `TODO-1D-AMX1-AXIAL-MIXING-FLUID-API-HANDOFF-2026-07-22`
- `TODO-SOURCE-PROPERTY-NOMINAL-TRAIN-RELEASE-PREFLIGHT-2026-07-22`
- `TODO-THESIS-FIGTABLE-MODEL-FORM-AND-BLOCKED-SCORECARD-PANELS-2026-07-22`

## Recommended Execution Order

1. Run `TODO-S13-UPCOMER-EXCHANGE-QWALL-MESH-GCI-UQ-GATE-2026-07-22`.
2. Keep `TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-PRODUCTION-HARVEST-UQ-2026-07-21` trigger-gated unless the same-QOI and mesh/GCI gates pass.
3. In parallel with non-overlapping files, run `TODO-THESIS-LATEX-CH4-REDUCTION-SPLIT-SYNC-2026-07-22`.
4. Run `TODO-SOURCE-PROPERTY-NOMINAL-TRAIN-RELEASE-PREFLIGHT-2026-07-22` to reduce friction before any S11/S15 candidate-specific gate.
5. Run `TODO-1D-AMX1-AXIAL-MIXING-FLUID-API-HANDOFF-2026-07-22` if the priority is model progress rather than writing.
6. Run `TODO-THESIS-FIGTABLE-MODEL-FORM-AND-BLOCKED-SCORECARD-PANELS-2026-07-22` to harvest thesis value from current negative/diagnostic evidence.

## Agent Prompts

### Chapter 4 Writer

Claim `TODO-THESIS-LATEX-CH4-REDUCTION-SPLIT-SYNC-2026-07-22`. Use the thesis tomorrow handoff, master model-form scoreboard, source/property policy, and completed Chapter 5/6 syncs. Produce a papers-board-safe Chapter 4 LaTeX sync that explains CFD-to-1D reduction, runtime inputs, evidence classes, split roles, source/property labels, and why diagnostic evidence does not imply admission.

### S13 Mesh/GCI Gate

Claim `TODO-S13-UPCOMER-EXCHANGE-QWALL-MESH-GCI-UQ-GATE-2026-07-22`. Build a read-only matrix for direct `Q_wall_W`, `mdot_exchange`, `tau_recirc`, and wall/core/bulk thermal contrast versus available mesh/GCI evidence. Fail closed if the same-QOI mesh or time uncertainty evidence is absent.

### AMX1 Handoff

Claim `TODO-1D-AMX1-AXIAL-MIXING-FLUID-API-HANDOFF-2026-07-22`. Do not edit Fluid. Convert the AMX1 dry contract into an exact external implementation packet: config schema, solver hooks, conservative ledger equations, tests, Salt2 smoke criteria, source/property labels, and stop/go gates.

### Source/Property Preflight

Claim `TODO-SOURCE-PROPERTY-NOMINAL-TRAIN-RELEASE-PREFLIGHT-2026-07-22`. Build a row-level release audit for Salt1-4 nominal train rows independent of any single candidate. The output should tell S11/S15 exactly which labels, source envelopes, and property modes block candidate release.

### Thesis Figure/Table Builder

Claim `TODO-THESIS-FIGTABLE-MODEL-FORM-AND-BLOCKED-SCORECARD-PANELS-2026-07-22`. Generate SVG/CSV/caption-ledger panels from completed evidence: model-form ladder, blocked freeze waterfall, sensor/QOI projection uncertainty, pressure negative result, and S13 diagnostic-only panel. Keep all final predictive score values at `0`.

## Do Not Do

- Do not duplicate the active S13 same-QOI neighbor-window row.
- Do not run production harvest until S13 same-QOI and mesh/GCI gates pass.
- Do not relabel source-side heat flow as direct wall heat.
- Do not fit, tune, select, or admit a closure from coordinator rows.
- Do not consume validation/holdout/external-test rows before a frozen runtime-legal candidate exists.
- Do not mutate native CFD/OpenFOAM outputs, registry/admission state, scheduler jobs, Fluid, or external papers from this coordination task.
