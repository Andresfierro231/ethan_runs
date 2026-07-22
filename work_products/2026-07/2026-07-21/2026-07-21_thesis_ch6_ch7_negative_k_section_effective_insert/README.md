---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_negative_k_section_effective_thesis_case_dispatch/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
tags: [thesis, negative-k, section-effective, ch6, ch7]
related:
  - .agent/status/2026-07-21_TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21.md
  - .agent/journal/2026-07-21/thesis-ch6-ch7-negative-k-section-effective-insert.md
  - imports/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert.json
task: TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Thesis Ch6/Ch7 Negative-K Section-Effective Insert

## Result

Inserted the negative-K / section-effective lower-right corner result into the
current CSEM thesis dossier:

- Ch. 6 now states the component-K forcing path is closed for current
  `corner_lower_right` rows and gives the signed residual values.
- Ch. 7 now presents the no-fit bakeoff result as thesis evidence only.
- The figure/table ledger now routes the case memo, no-fit performance table,
  and residual ownership table into Ch. 6/Ch. 7.

## Assumptions

The current Salt2/Salt3/Salt4 `corner_lower_right` rows are final-training
method-context rows, not validation, holdout, or external-test rows. The
section-effective residual can be discussed because it is already frozen in
source packages, but no coefficient admission follows from that discussion.

The available F3/Shah apparent baseline artifacts are status/readiness
artifacts. They explicitly withhold numeric F3-vs-F6 comparison until an
ordinary admissible F6 candidate exists, so the thesis text does not claim a
numeric F3/Shah victory.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, validation/holdout/external score, fitting, tuning,
model selection, closure admission, component-K/F6/cluster-K promotion, clipped
K, hidden/global multiplier, blocker register, generated index, or
runtime-leakage relaxation was changed.

## Package Files

- `insertion_ledger.csv` records the exact thesis-current files and sections
  touched by this insertion.
- `thesis_claim_boundary_update.md` gives copy-ready allowed and forbidden
  pressure claims.
- `pressure_claim_boundary_table.csv` is a compact table for Chapter 6 or a
  methods appendix.
- `caption_bank.md` provides guarded table/figure captions.
- `source_manifest.csv` records the frozen evidence packages and chapter files
  used by this insertion.
- `summary.json` gives the machine-readable task outcome and mutation flags.

## Thesis Use

Use this package where the thesis needs a rigorous negative result: current
lower-right two-tap pressure rows failed ordinary coefficient admission, but
they still provide useful section-effective residual evidence. The safe
short-form wording is:

> Current lower-right pressure rows are not admitted as ordinary component
> `K`, cluster `K`, F6, clipped `K`, or a hidden/global multiplier. They are
> preserved as recirculating section-effective residual evidence motivating
> `Delta_p_recirc_section`.
