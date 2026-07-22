---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_nonrecirc_anchor_request/nonrecirculating_anchor_request.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_separated_admission_review/final_gate_review.csv
  - work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/legwise_anchor_inventory.csv
  - work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/harvest_readiness_queue.csv
tags: [pressure-ledger, two-tap, nonrecirculating-anchor, component-k, f6]
related:
  - .agent/status/2026-07-20_TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN.md
  - .agent/journal/2026-07-20/two-tap-nonrecirc-anchor-plan.md
  - operational_notes/07-26/18/2026-07-18_TWO_TAP_NEXT_CONTEXT_AND_STEPS.md
task: TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: work_product
status: complete
---
# Two-Tap Non-Recirculating Anchor Plan

Generated: `2026-07-20T15:55:17+00:00`

## Result

This planning package evaluates `NR-CLR-01` and `NR-ALT-01` from the July 18
non-recirculating-anchor request. The preferred future lane is `CAND-001`, a
same-topology `corner_lower_right` sampler from Salt4 high-heat/no-recirculation
probe cases after terminal review. It is conditional only: this row performs no
scheduler launch and emits no coefficient admission.

Current Salt2/Salt3/Salt4 `corner_lower_right` rows remain diagnostic only
because they fail reverse-flow, component-isolation, and same-QOI UQ gates.

## Outputs

- `candidate_anchor_inventory.csv`
- `source_case_selection.csv`
- `staging_contract.csv`
- `endpoint_sampling_contract.csv`
- `same_qoi_uq_family_plan.csv`
- `launch_or_no_launch_decision.json`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output was mutated. No registry/admission state was
mutated. No scheduler action, solver launch, postprocessing launch, F6 fit,
component-K admission, hidden multiplier, clipped K, or endpoint-pressure
invention was performed.
