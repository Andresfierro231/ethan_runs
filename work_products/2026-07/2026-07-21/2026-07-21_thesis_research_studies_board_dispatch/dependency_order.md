---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/study_portfolio.csv
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/README.md
tags: [thesis-dossier, research-studies, dependency-order, forward-model]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/README.md
task: TODO-THESIS-RESEARCH-STUDIES-BOARD-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Study Dependency Order

## Immediate Writing Path

1. Close or archive `TODO-PRED-FIRST-KEY-STUDIES-WAVE-2026-07-21`.
2. Claim `TODO-THESIS-S0-S3-FIRST-WAVE-WRITING-INTEGRATION-2026-07-21`.
3. Write S0-S3 into the thesis as baseline infrastructure, external-BC
   readiness, split heat-loss evidence, and pressure source-envelope
   non-admission.

This path needs no new CFD, Fluid run, fitting, or admission.

## Scientific Path

1. Finish heat-loss Phase 3 before another wall/test-section thesis conclusion.
2. Run S4 recirculation guard before any upcomer/test-section row is described
   as ordinary single-stream pipe evidence.
3. Run S5 source/property split release before any candidate freeze.
4. Run S6 only after S1-S5 pass and one runtime-legal candidate is frozen in
   advance of scoring.

## Figure/Table Path

1. Use S0-S3 outputs for immediate tables after first-key closeout.
2. Add heat and pressure waterfalls only after their residual source tables are
   present and labeled.
3. Add recirculation guard map only after S4 lands.
4. Add final scorecard only after S6 lands; otherwise use a blocked scorecard
   shell with `FINAL_FREEZE_TBD absent`.

## Triggers

- S4 can start now from existing recirculation/onset/hybrid evidence.
- S5 can start now as a release-gate audit, but it cannot release a candidate
  unless source/property labels and split permissions pass.
- S6 cannot start until a frozen candidate exists.
- Quantitative figure/table assembly should wait for the source study packages
  it visualizes.

## Stop Conditions

Stop and publish a blocked handoff instead of filling gaps if any study needs:

- CFD `mdot`, realized `wallHeatFlux`, validation temperatures, holdout
  temperatures, or external-test temperatures as runtime inputs;
- component K, F6, ordinary upcomer `Nu`, ordinary upcomer `f_D`, or ordinary
  upcomer K admission from current diagnostic rows;
- model selection from support, holdout, external, PM10, or future CFD rows.
