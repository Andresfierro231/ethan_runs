---
provenance:
  - .agent/BOARD.md
  - operational_notes/07-26/21/2026-07-21_THESIS_LATEX_TOMORROW_HANDOFF.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/latex_sync_contract.csv
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
tags: [thesis, numerical-studies, board-dispatch, csem, figures-tables]
related:
  - TODO-THESIS-N1-FROZEN-RUNTIME-LEGAL-CANDIDATE-GATE-2026-07-21
  - TODO-THESIS-N2-UPCOMER-EXCHANGE-QWALL-UQ-PAPER-PANELS-2026-07-21
  - TODO-THESIS-N3-THERMAL-RESIDUAL-OWNER-TRAIN-ABLATION-2026-07-21
  - TODO-THESIS-N4-SENSOR-QOI-PROJECTION-UNCERTAINTY-TABLE-2026-07-21
  - TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21
task: TODO-THESIS-LATEX-CH5-WRITE-AND-NUMERICAL-STUDY-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: work-product
status: reference
supersedes: []
superseded_by:
---
# Thesis Numerical Studies Dispatch

This package records the main-board numerical studies that most directly
strengthen the CSEM thesis after the Chapter 5 LaTeX model-form sync.

## Study Priority

| Study | Thesis value | Figure/table target |
| --- | --- | --- |
| N1 frozen runtime-legal candidate gate | Turns the current blocker logic into a clean Ch. 8 readiness table and prevents premature final-score claims. | Ch. 8 candidate gate table; runtime-input audit table. |
| N2 upcomer exchange Qwall/UQ paper panels | Converts recirculation visuals and sampled-field evidence into the figure set needed to justify the throughflow-plus-exchange model path. | Ch. 3/5 upcomer panels; Ch. 7 diagnostic exchange table. |
| N3 thermal residual-owner train ablation | Makes the heat-loss story quantitative without admitting nonphysical corrections or hiding residuals in internal Nu. | Ch. 7 thermal residual-owner figure/table. |
| N4 sensor/QOI projection uncertainty table | Clarifies what is scored, what is excluded, and what is never a runtime input. | Ch. 6 uncertainty table; Ch. 8 scorecard context. |
| Existing pressure no-fit bakeoff | Already on the board as `TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21`; use it for pressure negative-result and hybrid residual tables. | Ch. 7 pressure negative-result table and section-effective comparison. |

## Required Guardrails

- Do not run validation/holdout/external-test scoring before a freeze gate.
- Do not fit, tune, select, or admit coefficients inside diagnostic study rows.
- Do not promote ordinary upcomer `Nu`, `f_D`, `K`, component `K`, exchange-cell
  coefficients, or empirical leg-bias corrections from these rows.
- Do not use CFD mass flow, realized `wallHeatFlux`, imposed CFD cooler duty,
  validation temperatures, holdout rows, or external-test rows as predictive
  runtime inputs.

## Implementation Contract

Each numerical study should publish a dated package with:

- README with split role, admission state, allowed use, forbidden use, and
  runtime-leakage audit.
- CSV tables for the thesis figure/table target.
- A short caption/prose bank identifying the target LaTeX chapter.
- A validation command and result.
- Status, journal, and import manifest closeout.
