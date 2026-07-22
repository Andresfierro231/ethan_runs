---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/recirc_pressure_basis_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/residual_equation_contract.md
tags: [journal, pressure-ledger, two-tap, section-effective, hybrid-pressure]
related:
  - .agent/status/2026-07-21_TODO-TWO-TAP-SECTION-EFFECTIVE-HYBRID-PRESSURE-SCORECARD-2026-07-21.md
  - imports/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard.json
task: TODO-TWO-TAP-SECTION-EFFECTIVE-HYBRID-PRESSURE-SCORECARD-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
---
# Two-Tap Section-Effective Hybrid Pressure Scorecard

## Attempted

Built a task-owned scorecard package that turns the existing
`corner_lower_right` two-tap pressure evidence into a section-effective hybrid
pressure diagnostic. The package uses the frozen pressure-corner result, the
July 20 recirculating section-effective model, and the LitRev throughflow plus
recirculation exchange-cell residual contract.

## Observed

All three Salt2/Salt3/Salt4 rows remain section-effective and not admitted for
component `K` or F6. The gross static pressure rise is about `3035-3069 Pa`,
but the hydrostatic term accounts for essentially all of it. The available
signed residual after available corrections is small and negative:
`-1.25366731683 Pa`, `-1.84957005859 Pa`, and `-1.67833900273 Pa`.

Salt2-frozen diagnostic transfer using `K_eff_recirc=-7.56139965813` gives a
Salt3 error of about `0.217 Pa` and a Salt4 error of about `0.470 Pa`.

## Inferred

This gives a defensible thesis lane: the ideal ordinary component route fails,
but the evidence can still be quantified as a named recirculating
section-effective pressure residual. The result should be described as
diagnostic residual movement and pressure-basis separation, not as a closure
coefficient.

## Caveats

The oracle envelope is non-predictive. The Salt2-frozen transfer check is a
diagnostic transfer calculation only and is not validation, holdout, or
external-test scoring. Same-QOI UQ and ordinary low-recirculation anchors remain
missing for admission.

## Next Useful Actions

Use this package as the pressure table source for thesis language about
section-effective pressure modeling. A future admitted hybrid route still needs
split-safe scoring, same-QOI UQ, and a pressure model comparison against the
current baseline without clipping, hidden multipliers, or component-K promotion.
