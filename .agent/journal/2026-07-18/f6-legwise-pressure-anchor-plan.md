---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_nonrecirculating_pressure_anchor_plan/named_pressure_anchor_slots.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
  - work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/source_property_label_contract.csv
tags: [pressure-ledger, friction-closures, f6, recirculation, source-property]
related:
  - .agent/status/2026-07-18_AGENT-547.md
  - work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/README.md
task: AGENT-547
date: 2026-07-18
role: Hydraulics/Literature-synthesis/Implementer/Tester/Writer
type: journal
status: complete
---
# F6 Legwise Pressure Anchor Plan

## Attempted

Implemented a package-local, reproducible builder/test pair for the requested
leg-by-leg F6 pressure-anchor path. The builder consumes the prior F6
nonrecirculating-anchor plan, the landed two-tap endpoint pressure/basis audit,
and source/property label carryforward evidence.

## Observed

The raw endpoint basis is finite for the three harvested `corner_lower_right`
feature pairs. Same-window recirculation metrics are also finite, but all three
feature pairs fail ordinary recirculation gates with material reverse flow
(`aggregate_RAF` about 0.763 and `aggregate_RMF` about 0.500).

The resulting inventory contains 36 leg/slot rows, including six ordinary
straight-candidate slots that remain blocked because endpoint/UQ gates are not
attached, six non-upcomer reverse-flow diagnostic slots, eighteen
component/junction diagnostic rows, and six blocked missing-endpoint rows. No
row is ordinary F6 fit-eligible or admission-review eligible today.

## Inferred

Leg-by-leg analysis is useful, but current evidence does not support assuming
recirculation is limited to the upcomer. The finite endpoint evidence now shows
material reverse flow at the lower-right feature pair too. The safer thesis
framing is: ordinary straight-leg F6 requires low-reverse pressure anchors;
upcomer pressure closure should be a separate throughflow-plus-recirculation
model lane; component/junction endpoint pairs remain diagnostic unless their
own isolation and same-QOI UQ gates pass.

## Contradictions / Caveats

The package does not resolve component isolation, straight-reference/development
loss, or same-QOI mesh/time UQ. It also does not score against
`F3_shah_apparent`; it only defines the future admission gate. This is
intentional because the current evidence is not sufficient for F6 fitting or
component-K admission.

## Next Useful Actions

Run a separate admission-review package only after candidate straight-leg rows
have finite endpoint pressure, velocity, RAF/RMF/SVF, geometry-normalized
straight/development terms, and same-QOI UQ. For upcomer, build a separate
throughflow-plus-recirculation pressure closure and compare it against
`F3_shah_apparent` without a hidden global multiplier.
