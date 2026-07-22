---
provenance:
  - .agent/BOARD.md
  - .agent/BLOCKERS.md
  - .agent/STATE.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_predictive_study_figure_table_package/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s5_source_property_split_release/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
tags: [thesis-dossier, next-studies, board-dispatch, scientific-plan, forward-model]
related:
  - operational_notes/07-26/21/2026-07-21_THESIS_NEXT_STUDIES_BOARD_DISPATCH.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/README.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
task: TODO-THESIS-NEXT-STUDIES-BOARD-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis Next Studies Board Dispatch

## Decision

The completed S0-S5 packages and the figure/table package make the thesis
scientific queue visible, but they do not yet produce a frozen runtime-legal
candidate. The next board wave should therefore focus on the evidence that can
unblock or falsify a candidate before S6:

- S7: sensor-map contract for TP/TW score interpretation.
- S8: wall/test-section axial-mixing or setup-only thermal candidate.
- S9: upcomer onset anchor and exchange-QOI uncertainty requirements.
- S10: pressure/F6 low-recirculation anchor and same-QOI UQ decision.
- S11: narrow source/property/split refresh only for an admission-worthy
  physical candidate.

S6 remains trigger-gated. No final predictive accuracy, component K, F6,
ordinary upcomer `Nu`, ordinary upcomer `f_D`, or ordinary upcomer K claim is
allowed until the relevant study explicitly admits it.

## Files In This Package

| File | Use |
| --- | --- |
| `next_study_portfolio.csv` | One-row-per-study map for S7-S11 plus the negative-results writing package. |
| `execution_sequence.md` | Decision-complete order for future agents, including rows to claim rather than duplicate. |
| `board_rows_added.md` | Human-readable summary of the board rows added by this dispatch. |
| `source_manifest.csv` | Exact source files used to justify this dispatch and the guardrails inherited by follow-on rows. |
| `summary.json` | Machine-readable package summary. |

## Required Execution Standard

Before claiming S7-S11 or the negative-results row, open:

- `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/study_execution_workflow.md`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/per_study_execution_packets.md`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/claim_admission_rules.md`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/validation_checklist.md`

Those files define the required README, summary JSON, source manifest,
acceptance gate matrix, runtime leakage audit, figure/table manifest, status,
journal, and import-manifest contract for each study.

## Current Board Routes

| Need | Board route | Status |
| --- | --- | --- |
| TP/TW sensor map | `TODO-THESIS-STUDY-S7-SENSOR-MAP-TP-TW-CONTRACT-2026-07-21` and existing `TODO-PRED-SENSOR-MAP` | Open; coordinate to avoid duplicate technical work. |
| Wall/test-section candidate | `TODO-THESIS-STUDY-S8-WALL-TEST-SECTION-AXIAL-MIXING-CANDIDATE-2026-07-21` | Open. |
| Upcomer onset and exchange UQ | `TODO-THESIS-STUDY-S9-UPCOMER-ONSET-ANCHOR-EXCHANGE-UQ-2026-07-21` | Open; no sampler launch unless separately claimed. |
| Pressure/F6 low-recirculation anchor | `TODO-THESIS-STUDY-S10-PRESSURE-F6-LOW-RECIRC-ANCHOR-UQ-2026-07-21` | Open; coordinate with same-QOI UQ phase rows. |
| Candidate-specific source/property refresh | `TODO-THESIS-STUDY-S11-CANDIDATE-SOURCE-PROPERTY-REFRESH-2026-07-21` | Trigger-gated after S8, S9, or S10 admits a physical candidate. |
| Frozen candidate scorecard | Existing `TODO-THESIS-STUDY-S6-FROZEN-CANDIDATE-SCORECARD-2026-07-21` | Do not duplicate; wait for a frozen runtime-legal candidate. |
| Figure export and caption polish | Existing `TODO-THESIS-FIGURES-DIAGRAMS` | Claim existing row; do not create a duplicate export row. |
| Negative-results contribution | `TODO-THESIS-NEGATIVE-RESULTS-SCIENTIFIC-CONTRIBUTION-SECTION-2026-07-21` | Open. |

## Scientific Contribution Target

The thesis can benefit from publishing negative and gatekeeping results as
scientific findings, not just blockers. The strongest near-term contribution is
to show how the workflow rejects tempting but invalid closures:

- recirculating upcomer rows are not ordinary single-stream `Nu/f_D/K` evidence;
- two-tap pressure rows are diagnostic until isolation, recirculation, and
  same-QOI UQ gates pass;
- source/property and split labels prevent hidden training leakage;
- final scorecard shells are useful precisely because they make absent frozen
  candidates visible.

## Guardrails

Follow-on studies must preserve runtime-input discipline. Do not use CFD
`mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty, realized
test-section heat, validation temperatures, holdout temperatures, or
external-test temperatures as predictive runtime inputs. Do not mutate native
solver outputs, registry/admission state, scheduler state, Fluid source, or
external repos from these thesis-dispatch rows.
