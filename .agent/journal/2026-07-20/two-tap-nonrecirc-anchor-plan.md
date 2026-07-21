---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/source_case_selection.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/endpoint_sampling_contract.csv
tags: [pressure-ledger, two-tap, nonrecirculating-anchor]
related:
  - .agent/status/2026-07-20_TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN.md
  - imports/2026-07-20_two_tap_nonrecirc_anchor_plan.json
task: TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: journal
status: complete
---
# Two-Tap Non-Recirculating Anchor Plan

## Attempted

Implemented the planning-only two-tap non-recirculating anchor task requested
by the current handoff. The package selects candidate source families and writes
staging, endpoint sampling, and same-QOI UQ contracts for a later sampler row.

## Observed

The current harvested Salt2/Salt3/Salt4 `corner_lower_right` rows remain
diagnostic only. Their raw pressure/velocity basis is finite, but reverse-flow,
component-isolation, and same-QOI UQ gates still fail.

## Inferred

The best next lane is still same-topology `corner_lower_right`, but only from a
future low-reverse source case. The preferred conditional source family is the
Salt4 high-heat/no-recirculation probe group after terminal review. PM10
corrected-Q rows are secondary and require terminal/admission refresh. Alternate
named two-tap features are deferred until exact mesh-station labels and
low-reverse evidence exist.

## Caveats

This package does not launch, harvest, fit, or admit anything. It leaves the
three current two-tap blockers open.

## Next Useful Actions

After terminal review of the Salt4 high-heat/no-recirculation jobs, claim a
fresh staged-copy cfd-pp sampler row if a source case passes preflight. That row
must produce finite endpoint fields and same-window RAF/RMF/SVF before any gate
review.
