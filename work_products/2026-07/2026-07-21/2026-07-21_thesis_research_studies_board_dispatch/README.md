---
provenance:
  - .agent/BOARD.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - operational_notes/maps/forward-predictive-model.md
tags: [thesis-dossier, research-studies, study-portfolio, board-dispatch, forward-model]
related:
  - operational_notes/07-26/21/2026-07-21_THESIS_RESEARCH_STUDIES_BOARD_DISPATCH.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/README.md
task: TODO-THESIS-RESEARCH-STUDIES-BOARD-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis Research Studies Board Dispatch

## Decision

The thesis should continue on two tracks:

- Write now from existing evidence: S0-S3 consolidation, current CSEM chapter
  drafts, LitRev incorporation, pressure non-admission, split heat-loss
  evidence, and SAM/CSEM limitations.
- Run or consolidate only the missing studies needed for final predictive
  claims: S4 recirculation guard, S5 source/property split release, and S6
  frozen candidate scorecard.

S0-S3 are not reissued as implementation studies here because
`TODO-PRED-FIRST-KEY-STUDIES-WAVE-2026-07-21` already covers them. The only
new S0-S3 row is a writing-integration row that should wait until the first-key
package is closed out on the board.

## Files In This Package

| File | Use |
| --- | --- |
| `study_portfolio.csv` | One-row-per-study map from S0-S6 to board row, analysis need, thesis target, outputs, blockers, and guardrails. |
| `figure_table_wishlist.csv` | Concrete requested figures/tables, including source data dependencies and target thesis sections. |
| `dependency_order.md` | Execution sequence and trigger rules. |
| `board_row_proposals.md` | Human-readable summary of rows added to `.agent/BOARD.md` and rows intentionally not duplicated. |

## Current Board Dispatch

| Area | Board route | Status |
| --- | --- | --- |
| S0-S3 evidence consolidation | `TODO-PRED-FIRST-KEY-STUDIES-WAVE-2026-07-21` | Existing active row; do not duplicate. |
| S0-S3 writing | `TODO-THESIS-S0-S3-FIRST-WAVE-WRITING-INTEGRATION-2026-07-21` | New wait-for-closeout writing row. |
| S4 recirculation guard | `TODO-THESIS-STUDY-S4-RECIRCULATION-GUARD-UPCOMER-HYBRID-2026-07-21` | New open study row. |
| S5 release gate | `TODO-THESIS-STUDY-S5-SOURCE-PROPERTY-SPLIT-RELEASE-2026-07-21` | New open study row. |
| S6 frozen scorecard | `TODO-THESIS-STUDY-S6-FROZEN-CANDIDATE-SCORECARD-2026-07-21` | New trigger-gated row. |
| Quantitative figures/tables | `TODO-THESIS-PREDICTIVE-STUDY-FIGURE-TABLE-PACKAGE-2026-07-21` | New evidence-gated row. |

## Writing Ready Now

- Motivation, CSEM contribution, and SAM relevance from current thesis
  sections.
- CFD evidence/database narrative, with CFD as high-fidelity reference rather
  than experimental validation.
- `fluid+walls` model form, runtime contract, split policy, and claim ledger.
- S0-S3 as infrastructure, diagnostics, release gates, and non-admission
  results once the first-key package is closed out.
- Pressure-corner/F6/component-K negative result as diagnostic non-admission.
- Heat-loss split evidence and runtime-leakage discipline.

## Blocked Until More Model Work

- Final predictive accuracy.
- Frozen candidate scorecard.
- Ordinary upcomer `Nu`, `f_D`, or K fits.
- Component K or F6 admission.
- Wall/test-section/passive thermal closure admission.
- Any SAM validation claim.

## Guardrails

No new result is admitted by this dispatch. Follow-on agents must preserve the
runtime leakage rules: no CFD `mdot`, realized `wallHeatFlux`, imposed cooler
duty, realized test-section heat, validation temperatures, holdout
temperatures, or external-test temperatures as predictive runtime inputs.
