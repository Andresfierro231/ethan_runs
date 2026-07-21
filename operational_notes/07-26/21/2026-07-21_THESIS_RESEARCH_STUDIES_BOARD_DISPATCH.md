---
provenance:
  - .agent/BOARD.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/README.md
tags: [thesis-dossier, research-studies, forward-model, board-dispatch, writing-handoff]
related:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/README.md
task: TODO-THESIS-RESEARCH-STUDIES-BOARD-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: operational_note
status: complete
supersedes: []
superseded_by:
---
# Thesis Research Studies Board Dispatch

## Why This Avenue Exists

The thesis writing thread has enough current evidence to keep drafting, but
the final predictive-model claim is still blocked. The right next move is to
separate writing-ready evidence from research studies that must still be run,
and to put those studies on the board with exact analysis and figure/table
contracts.

This dispatch does not create new CFD, run Fluid, tune a model, or admit a
closure. It turns the existing S0-S6 roadmap into claimable work while avoiding
duplicate implementation of S0-S3, which is already covered by
`TODO-PRED-FIRST-KEY-STUDIES-WAVE-2026-07-21`.

## Open First

1. `work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/README.md`
2. `work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/study_portfolio.csv`
3. `work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/figure_table_wishlist.csv`
4. `work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/dependency_order.md`
5. `reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md`
6. `work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/README.md`

## Trusted Packages

- S0-S3 consolidation:
  `work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/`
- Predictive roadmap:
  `reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md`
- Heat-loss Phase 0-2 packages:
  `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_0_baseline_release_gate/`,
  `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/`,
  and
  `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_2_split_heat_loss_evidence/`
- Pressure source-envelope publication freeze:
  `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/`
- Current thesis draft packet:
  `work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_current_draft_packet/`

## Unresolved Blockers

- No frozen final predictive candidate exists.
- S4 still needs a recirculation guard and hybrid upcomer evidence package.
- S5 still needs a release audit tying source/property labels to split
  permissions before any final candidate freeze.
- S6 is trigger-gated until S1-S5 pass and one frozen runtime-legal candidate
  is predeclared.
- Generated documentation indexes are currently read-only for this dispatch
  because `TODO-PRED-FIRST-KEY-STUDIES-WAVE-2026-07-21` owns them on the live
  board.

## Active Board Rows

- `TODO-THESIS-RESEARCH-STUDIES-BOARD-DISPATCH-2026-07-21`: this completed
  dispatch package.
- `TODO-PRED-FIRST-KEY-STUDIES-WAVE-2026-07-21`: S0-S3 consolidation package.
- `TODO-THESIS-S0-S3-FIRST-WAVE-WRITING-INTEGRATION-2026-07-21`: write S0-S3
  into thesis prose after the first-key row is closed out.
- `TODO-THESIS-STUDY-S4-RECIRCULATION-GUARD-UPCOMER-HYBRID-2026-07-21`: build
  recirculation disable/hybrid upcomer study.
- `TODO-THESIS-STUDY-S5-SOURCE-PROPERTY-SPLIT-RELEASE-2026-07-21`: build the
  source/property and split release gate.
- `TODO-THESIS-STUDY-S6-FROZEN-CANDIDATE-SCORECARD-2026-07-21`: trigger-gated
  frozen candidate scorecard.
- `TODO-THESIS-PREDICTIVE-STUDY-FIGURE-TABLE-PACKAGE-2026-07-21`: assemble
  quantitative figures/tables after source studies land.

## Next Task Sequence

1. Close or archive `TODO-PRED-FIRST-KEY-STUDIES-WAVE-2026-07-21`, then claim
   `TODO-THESIS-S0-S3-FIRST-WAVE-WRITING-INTEGRATION-2026-07-21`.
2. Claim S4 before interpreting current upcomer/test-section rows as ordinary
   single-stream closure evidence.
3. Claim S5 before freezing any candidate or reporting fit-enabled rows.
4. Claim S6 only after S1-S5 pass and the frozen candidate is named before
   scoring.
5. Claim the figure/table package after the study packages exist, so visuals
   cite real output artifacts rather than planned analyses.

## Output Contract

Every follow-on study should publish a README, source manifest, status,
journal, import manifest, and tables/figures named in
`figure_table_wishlist.csv`. Tables must separate observed CFD evidence,
diagnostic reductions, admitted runtime inputs, and score-only targets.

## Do-Not-Do Guardrails

- Do not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty,
  realized test-section heat, validation temperatures, holdout temperatures,
  or external-test temperatures as predictive runtime inputs.
- Do not admit F6, component K, ordinary upcomer `Nu`, ordinary upcomer `f_D`,
  ordinary upcomer K, or final predictive accuracy from this writing dispatch.
- Do not duplicate S0-S3 implementation while the first-key studies wave
  exists.
- Do not edit native CFD/OpenFOAM outputs, registry/admission state, scheduler
  state, Fluid source, external paper repos, or generated documentation indexes
  from this dispatch row.
