---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert/insertion_ledger.csv
tags: [thesis, claim-boundary, negative-k, section-effective]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
task: TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: note
status: complete
---
# Thesis Claim Boundary Update

## Allowed Claims

- Current lower-right corner two-tap rows are useful pressure-basis and
  recirculating-section diagnostics.
- Signed available residuals after hydrostatic and kinetic correction are
  Salt2 `-1.25366731683 Pa`, Salt3 `-1.84957005859 Pa`, and Salt4
  `-1.67833900273 Pa`.
- The no-fit Salt2-frozen diagnostic transfer has max Salt3/Salt4 error
  `0.47046606946166093438399 Pa`.
- The result motivates `Delta_p_recirc_section` as a section-effective residual
  ledger term.

## Forbidden Claims

- The current rows admit ordinary component `K`.
- The current rows admit cluster `K`, F6, clipped `K`, or a hidden/global
  hydraulic multiplier.
- The current hybrid term beats F3/Shah apparent numerically.
- The current hybrid term is freeze-ready or candidate-reviewable.
- The current result consumes validation, holdout, or external-test rows.

## Why This Matters

The negative result is now thesis-facing rather than merely a blocker. It shows
that the workflow can reject an attractive but invalid coefficient form and
still preserve the measured residual as evidence for a better reduced-model
structure.
