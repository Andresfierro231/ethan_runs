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
# Two-Tap Nonrecirculating Anchor Request

Generated: `2026-07-18T21:02:13.179443+00:00`

## Result

This request defines future evidence needed for ordinary two-tap closure work. It is not a scheduler launch and does not admit a coefficient.

## Outputs

- `nonrecirculating_anchor_request.csv`
- `launch_gate_contract.csv`
- `assumption_register.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output was mutated. No registry/admission state,
scheduler state, Fluid source, F6 fit, component-K admission, hidden multiplier,
clipped K, or endpoint-pressure invention was produced.
