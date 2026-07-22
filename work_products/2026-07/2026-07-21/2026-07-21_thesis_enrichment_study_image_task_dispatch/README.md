---
provenance:
  - .agent/BOARD.md
  - .agent/BLOCKERS.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_next_studies_board_dispatch/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s6_frozen_candidate_scorecard/README.md
tags: [thesis-dossier, board-dispatch, enrichment, figures, tables, next-studies]
related:
  - operational_notes/07-26/21/2026-07-21_THESIS_ENRICHMENT_STUDY_IMAGE_TASK_DISPATCH.md
  - .agent/status/2026-07-21_TODO-THESIS-ENRICHMENT-STUDY-IMAGE-TASK-DISPATCH-2026-07-21.md
task: TODO-THESIS-ENRICHMENT-STUDY-IMAGE-TASK-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis Enrichment Study Image Task Dispatch

## Decision

The highest-value thesis studies are already on the board as S7-S11 plus the
negative-results contribution row. This dispatch adds the missing granularity:
claimable figure/table tasks that turn those studies into thesis-enriching
visuals without duplicating scientific work or changing admission state.

## Files

| File | Use |
| --- | --- |
| `high_value_board_coverage.csv` | Maps each main thesis weakness to a live board task and expected evidence output. |
| `image_table_task_queue.csv` | Granular figure/table tasks added to the board, with target chapters and gating. |
| `execution_order.md` | Recommended order for agents to claim studies and visual packages. |
| `board_rows_added.md` | Human-readable summary of the rows added by this dispatch. |
| `source_manifest.csv` | Exact source files used. |
| `summary.json` | Machine-readable dispatch counts. |

## Highest-Value Existing Study Rows

- `TODO-THESIS-STUDY-S7-SENSOR-MAP-TP-TW-CONTRACT-2026-07-21`
- `TODO-THESIS-STUDY-S8-WALL-TEST-SECTION-AXIAL-MIXING-CANDIDATE-2026-07-21`
- `TODO-THESIS-STUDY-S9-UPCOMER-ONSET-ANCHOR-EXCHANGE-UQ-2026-07-21`
- `TODO-THESIS-STUDY-S10-PRESSURE-F6-LOW-RECIRC-ANCHOR-UQ-2026-07-21`
- `TODO-THESIS-STUDY-S11-CANDIDATE-SOURCE-PROPERTY-REFRESH-2026-07-21`
- `TODO-THESIS-NEGATIVE-RESULTS-SCIENTIFIC-CONTRIBUTION-SECTION-2026-07-21`

## Figure/Table Rows Added

- `TODO-THESIS-FIGTABLE-S7-SENSOR-MAP-OVERLAY-2026-07-21`
- `TODO-THESIS-FIGTABLE-S8-WALL-TS-RESIDUAL-ATLAS-2026-07-21`
- `TODO-THESIS-FIGTABLE-S9-UPCOMER-EXCHANGE-EVIDENCE-2026-07-21`
- `TODO-THESIS-FIGTABLE-S10-PRESSURE-F6-GATE-WATERFALL-2026-07-21`
- `TODO-THESIS-FIGTABLE-S6-BLOCKED-SCORECARD-SHELL-2026-07-21`
- `TODO-THESIS-FIGTABLE-CROSS-CHAPTER-VISUAL-LEDGER-2026-07-21`

## Guardrails

Do not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty,
realized test-section heat, validation temperatures, holdout temperatures, or
external-test temperatures as predictive runtime inputs. Do not admit pressure
component K, F6, ordinary upcomer `Nu/f_D/K`, wall/test-section closure, or
final predictive accuracy from these dispatch or figure/table rows.
