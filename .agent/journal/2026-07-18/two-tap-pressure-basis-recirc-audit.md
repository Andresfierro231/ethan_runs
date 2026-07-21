---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/raw_endpoint_pressure_velocity.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/gate_decision_table.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/basis_field_contract.csv
tags: [pressure-ledger, two-tap, raw-endpoints, recirculation]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-PRESSURE-BASIS-RECIRC-AUDIT.md
  - imports/2026-07-18_two_tap_pressure_basis_recirc_audit.json
  - .agent/blockers.yml
task: TODO-TWO-TAP-PRESSURE-BASIS-RECIRC-AUDIT
date: 2026-07-18
role: Hydraulics/Tester/Implementer/Writer
type: journal
status: complete
---
# Two-Tap Pressure Basis Recirculation Audit

## Attempted

Built the first post-harvest audit package for `corner_lower_right`. The script
pairs upstream/downstream raw endpoint rows by case, computes separated
pressure/velocity basis terms, aggregates RAF/RMF/SVF, and emits gate decisions
without fitting F6 or admitting component K.

## Observed

All six raw endpoint rows are sampled. Each Salt2/Salt3/Salt4 feature pair has
finite static pressure, `p_rgh`, density, bulk velocity, local dynamic pressure,
hydrostatic correction, and kinetic correction.

Every pair fails the ordinary recirculation gate. Aggregate RAF is about
`0.763`; aggregate RMF is about `0.500`. These values are far above the
predeclared `<0.01` thresholds.

## Inferred

The raw pressure/velocity basis blocker is resolved for these three rows, but
ordinary component-K use remains blocked by material reverse flow. Any future
use should route through apparent/cluster or section-effective diagnostics, or
through a new non-recirculating anchor, rather than clipping K or tuning F6.

## Caveats

`K_apparent_diagnostic` is emitted only as a basis diagnostic because local
dynamic pressures are very small under the sampled recirculating flow. The
audit does not select a straight reference, attach same-QOI uncertainty, admit
component K, or export F6 evidence.

## Next Useful Actions

Run a component-isolation/apparent-cluster decision package, then a same-QOI
uncertainty status package. If the goal is ordinary F6 or component K, this
feature requires a different non-recirculating anchor or an explicitly
recirculation-modeled diagnostic pathway.
