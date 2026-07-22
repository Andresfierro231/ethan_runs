---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_predictive_study_figure_table_package/figure_to_claim_crosswalk.csv
tags: [figures, captions, thesis-dossier]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_predictive_study_figure_table_package/README.md
task: TODO-THESIS-PREDICTIVE-STUDY-FIGURE-TABLE-PACKAGE-2026-07-21
date: 2026-07-21
role: Figures/Writer/Reviewer/Implementer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Caption Bank

**PV-01. Predictive study gate flow.** S0-S5 are complete as release-gate,
diagnostic, and non-admission studies; S6 remains blocked because no
runtime-legal final candidate is frozen.

**PV-02. Baseline control surface.** The current baseline is a legal reference
surface with zero runtime leakage and no final accuracy claim.

**PV-03. Split-use permissions.** Train, support, holdout, external, and future
rows are separated before any fitting or scoring; holdout and external rows are
score-only after freeze.

**PV-04. External-BC coverage.** Segment and patch roles are either setup-facing
or explicitly unavailable. Missing setup fields are not filled from realized
CFD response variables.

**PV-05. Heat-path residual ownership.** Thermal residuals are assigned to
named heat paths and unresolved lanes. Internal Nu is not used as a residual
cleanup multiplier.

**PV-06. Pressure source-envelope result.** Current pressure-corner/F6 evidence
is diagnostic or section-effective only. Component K, clipped K, F6, and hidden
global multipliers remain inadmissible.

**PV-07. Recirculation guard.** Current upcomer evidence disables ordinary
single-stream Nu, f_D, and K fits and motivates a throughflow-plus-recirculation
model form.

**PV-08. Source/property release ledger.** Source/property labels are auditable,
but the release gate remains closed with zero fit/model-selection rows.

**PV-09. Blocked final scorecard shell.** The final scorecard is intentionally
empty until a predeclared frozen candidate exists and all release gates pass.
