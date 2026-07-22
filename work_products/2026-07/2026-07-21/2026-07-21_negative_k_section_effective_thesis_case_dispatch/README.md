---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/three_level_score.csv
tags: [pressure-ledger, negative-result, section-effective, hybrid-pressure, thesis]
related:
  - .agent/status/2026-07-21_TODO-NEGATIVE-K-SECTION-EFFECTIVE-THESIS-CASE-DISPATCH-2026-07-21.md
  - .agent/journal/2026-07-21/negative-k-section-effective-thesis-case-dispatch.md
  - imports/2026-07-21_negative_k_section_effective_thesis_case_dispatch.json
task: TODO-NEGATIVE-K-SECTION-EFFECTIVE-THESIS-CASE-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Tester/Reviewer
type: work_product
status: complete
---
# Negative-K Section-Effective Thesis Case Dispatch

## Decision

Stop trying to force ordinary component `K` from the current
`corner_lower_right` two-tap rows. The current rows should be published as a
negative coefficient-admission result and as positive evidence for a
section-effective recirculating pressure-residual model form.

This is not a retreat from the pressure finding. It is the scientifically useful
result: the literature review and the CFD evidence agree that a local
pressure-increase / negative apparent `K` signal can arise from pressure basis,
hydrostatic dominance, recovery, source definition, and recirculating endpoint
planes. The current rows fail the ordinary gates needed for component `K`, but
they do quantify a named section-effective residual.

## What Was Tested

The existing hybrid pressure scorecard was rerun without changing coefficients
or consuming protected rows. It scored the current Salt2/Salt3/Salt4
`corner_lower_right` rows at three levels:

- observed decomposition;
- Salt2-frozen diagnostic transfer;
- oracle upper bound, explicitly nonpredictive.

The Salt2-frozen diagnostic transfer has max Salt3/Salt4 absolute error
`0.47046606946166093438399 Pa`, or `0.01550084787332213673792019733%` of gross
Salt4 static rise. That supports thesis-scale quantification of the residual,
not model admission.

## Outputs

- `case_memo.md`
- `evidence_ledger.csv`
- `board_task_proposals.csv`
- `model_performance_summary.csv`
- `validation_commands.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

This package changes no model coefficients and admits no component `K`, cluster
`K`, F6 term, clipped `K`, hidden/global multiplier, validation score, holdout
score, external-test score, S11/S15/S6 trigger, source/property release, or
registry state.
