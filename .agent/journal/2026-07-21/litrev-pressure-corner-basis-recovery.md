---
task: TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: journal
status: complete
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/recirc_pressure_basis_table.csv
tags: [pressure-ledger, pressure-corner, two-tap, section-effective, litrev-synthesis]
related:
  - .agent/status/2026-07-21_TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY.md
  - imports/2026-07-21_litrev_pressure_corner_basis_recovery.json
  - operational_notes/maps/pressure-and-momentum-budget.md
---
# LitRev Pressure-Corner Basis Recovery

## Attempted

Claimed `TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY` as Hydraulics / cfd-pp / Tester / Writer and built a package-local reproducible audit under `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/`.

Opened the required LitRev pressure-corner findings, CFD postprocessing contract, current two-tap endpoint harvest packages, and the pressure-and-momentum topic map. Used the July 18 pressure/velocity basis audit plus July 20 section-effective and lower-right admission repair packages as the numeric evidence.

## Observed

The three current pressure-increasing corner candidates are Salt2/Salt3/Salt4 `corner_lower_right` endpoint pairs. Gross static pressure rises about 3.0 kPa downstream-minus-upstream. Hydrostatic correction is about the same magnitude and slightly larger than the gross static rise. Kinetic correction is small and negative. The same-endpoint available residual after hydrostatic and kinetic correction is negative, about `-1.25` to `-1.85 Pa`.

All three rows still have material reverse flow (`RAF` about `0.76`, `RMF` about `0.50`), apparent-cluster-only isolation, missing same-QOI UQ, and missing same-basis straight/developing reference.

## Inferred

The gross static pressure rise is not negative loss. It is primarily hydrostatic head, with a small kinetic/recovery contribution and a signed negative available residual that must remain diagnostic. Because recovery diagnostics and ordinary-flow gates are missing, the row cannot be named admitted `pressure_recovery` or `component_K`.

The correct current label is `section_effective`: useful for a recirculating pressure-residual model form, not for ordinary single-stream component K, F6 fitting, or a hidden global multiplier.

## Contradictions Or Caveats

The audit can close the available decomposition `dp_static = dp_hydrostatic + dp_kinetic + dp_available_residual`, but cannot complete a full irreversible-loss decomposition because same-basis straight/developing terms are blocked. Therefore the negative residual is not a source-defined negative coefficient.

## Next Useful Actions

Use the nonrecirculating anchor lane or a calibrated recirculating section-effective model to obtain recovery diagnostics, same-basis straight/developing reference, face-level same-QOI pressure/velocity uncertainty, and a throughflow dynamic-pressure basis before any coefficient admission review.
