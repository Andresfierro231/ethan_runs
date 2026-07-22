---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_negative_k_section_effective_thesis_case_dispatch/README.md
tags: [journal, pressure-ledger, negative-k, section-effective]
related:
  - .agent/status/2026-07-21_TODO-NEGATIVE-K-SECTION-EFFECTIVE-THESIS-CASE-DISPATCH-2026-07-21.md
  - imports/2026-07-21_negative_k_section_effective_thesis_case_dispatch.json
task: TODO-NEGATIVE-K-SECTION-EFFECTIVE-THESIS-CASE-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Tester/Reviewer
type: journal
status: complete
---
# Negative-K Section-Effective Thesis Case Dispatch

## Attempted

Reviewed the existing LitRev pressure-corner rules, basis-recovery audit,
publication freeze, and two-tap section-effective hybrid pressure scorecard.
Added a board row for the consolidation task and two proposed successor rows.
Created a work-product package and operational handoff to make the negative-K
reasoning findable without chat context.

## Observed

The source packages agree that current `corner_lower_right` rows are
section-effective diagnostics. They have gross static pressure rise near
`3.0 kPa`, hydrostatic dominance, small signed negative residuals after basis
correction, and material reverse-flow diagnostics. The scorecard reports
Salt2/Salt3/Salt4 residuals of `-1.25366731683`, `-1.84957005859`, and
`-1.67833900273 Pa`.

## Inferred

The correct thesis move is to stop current component-K attempts, preserve the
negative sign, and use the result as evidence for a hybrid
throughflow-plus-recirculation pressure model form. The Salt2-frozen diagnostic
transfer is useful model-form stress evidence, but it is not a frozen predictive
candidate and does not open validation, holdout, or external scoring.

## Contradictions Or Caveats

Earlier language around local `K` can be misleading if it is read as ordinary
component admission. The durable docs now need to say explicitly that the
current rows are not component `K`, cluster `K`, F6, clipped `K`, or hidden
multiplier evidence.

## Next Useful Actions

1. Run the thesis insertion row for Ch6/Ch7 with exact file ownership.
2. Run the no-fit bakeoff row if F3/Shah apparent baseline artifacts are
   source-resolved and split-safe.
3. Keep ordinary component-K work closed for current rows unless a future task
   provides low-recirculation/nonrecirculating anchors and same-QOI UQ.
