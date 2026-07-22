---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/gate_decision_table.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/basis_field_contract.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/same_qoi_uncertainty_contract.csv
tags: [pressure-ledger, two-tap, gates]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-REMAINING-GATES-AND-ANCHOR-REQUEST.md
  - .agent/journal/2026-07-18/two-tap-remaining-gates-and-anchor-request.md
task: TODO-TWO-TAP-REMAINING-GATES-AND-ANCHOR-REQUEST
date: 2026-07-18
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Component Isolation Decision

Generated: `2026-07-18T21:02:13.117672+00:00`

## Result

All three rows are routed to `apparent_cluster_only`; no admissible straight reference supports ordinary K under the same-basis/no-clipping/recirculation guardrails.

## Outputs

- `component_isolation_audit.csv`
- `straight_reference_options.csv`
- `apparent_cluster_decision.json`
- `assumption_register.csv`
- `next_action_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output was mutated. No registry/admission state,
scheduler state, Fluid source, F6 fit, component-K admission, hidden multiplier,
clipped K, or endpoint-pressure invention was produced.
