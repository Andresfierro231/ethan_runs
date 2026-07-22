---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_nonrecirculating_pressure_anchor_plan/named_pressure_anchor_slots.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
  - work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/source_property_label_contract.csv
tags: [pressure-ledger, friction-closures, f6, recirculation, source-property]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - .agent/status/2026-07-18_AGENT-547.md
  - .agent/journal/2026-07-18/f6-legwise-pressure-anchor-plan.md
task: AGENT-547
date: 2026-07-18
role: Hydraulics/Literature-synthesis/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Legwise Pressure Anchor Plan

Generated: `2026-07-18T20:55:41+00:00`

## Result

This package turns the F6 pressure-anchor question into a legwise contract. It
keeps ordinary straight-leg F6, component/junction diagnostics, and upcomer
recirculation-modeled pressure closure as separate lanes. The landed two-tap
endpoint harvest provides finite raw pressure/velocity fields for three
`corner_lower_right` feature pairs, but the same-window recirculation metrics
fail the ordinary gate in all three cases.

## Counts

- Leg/slot inventory rows: `36`
- Finite endpoint feature pairs: `3`
- Material reverse-flow endpoint pairs: `3`
- Ordinary F6 fit-eligible rows: `0`
- Admission-review eligible rows: `0`

## Outputs

- `legwise_anchor_inventory.csv`
- `legwise_recirc_exclusion_mask.csv`
- `legwise_pressure_residual_contract.csv`
- `upcomer_recirc_pressure_closure_contract.csv`
- `f3_vs_legwise_f6_admission_gate.csv`
- `next_endpoint_harvest_queue.csv`
- `source_manifest.csv`
- `summary.json`
- `MONDAY_F6_CONTEXT_AND_JOB_OPTIONS.md`

## Guardrails

No native CFD/OpenFOAM output was mutated. No registry/admission state,
scheduler action, solver/postprocessing launch, Fluid edit, F6 fit,
component-K admission, model selection, hidden global multiplier, or endpoint
pressure invention was performed. The package is a planning and gate-carryforward
artifact only.

## Monday Continuation

Open `MONDAY_F6_CONTEXT_AND_JOB_OPTIONS.md` before launching any F6/pressure
work. Current guidance is to launch no duplicate weekend solver or harvester:
`3293924`, `3299610`, and `3299620` are already running, while `3295438` is
dependency-held as the selected-Q harvester. Monday launch options are
conditional on terminal job review and fresh board claims.
