---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/raw_endpoint_pressure_velocity.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/basis_field_contract.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/recirculation_metric_contract.csv
tags: [pressure-ledger, two-tap, raw-endpoints, recirculation]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-PRESSURE-BASIS-RECIRC-AUDIT.md
  - .agent/journal/2026-07-18/two-tap-pressure-basis-recirc-audit.md
task: TODO-TWO-TAP-PRESSURE-BASIS-RECIRC-AUDIT
date: 2026-07-18
role: Hydraulics/Tester/Implementer/Writer
type: work_product
status: complete
---
# Two-Tap Pressure Basis Recirculation Audit

Generated: `2026-07-18T20:43:37.766133+00:00`

## Result

This package consumes the six harvested `corner_lower_right` raw endpoint rows
and separates static pressure, `p_rgh`, hydrostatic correction, kinetic
correction, local density, bulk velocity, and local dynamic-pressure basis
terms. It also aggregates same-window endpoint RAF/RMF/SVF recirculation
metrics.

The raw pressure/velocity basis is finite for all three Salt2/Salt3/Salt4
feature pairs. Ordinary component-K admission remains blocked because all three
pairs fail the recirculation gate. Component isolation and same-QOI uncertainty
are not audited here and remain downstream tasks.

## Current Counts

- Feature pairs audited: `3`
- Basis resolved pairs: `3`
- Recirculation pass pairs: `0`
- Recirculation fail pairs: `3`
- Ordinary component-K candidates: `0`

## Outputs

- `pressure_velocity_basis_audit.csv`
- `endpoint_recirculation_metrics.csv`
- `gate_decision_table.csv`
- `next_action_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output was mutated. No registry/admission state, Fluid
source, F6 fit, component-K admission, model selection, or endpoint-pressure
invention was performed.
