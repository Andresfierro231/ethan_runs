---
task: TODO-PRESSURE-CORNER-PUBLICATION-FREEZE-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: journal
status: complete
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
tags: [pressure-ledger, pressure-corner, publication-freeze, section-effective]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-CORNER-PUBLICATION-FREEZE-2026-07-21.md
  - imports/2026-07-21_pressure_corner_publication_freeze.json
  - operational_notes/maps/pressure-and-momentum-budget.md
---
# Pressure-Corner Publication Freeze

## Attempted

Converted the July 21 pressure-corner basis/recovery audit into a publication-facing freeze package. The goal was not to create new science, but to protect the result from future sign drift and make it easy to compare later extraction rows against the same schema.

## Observed

The frozen canonical table contains three rows: Salt2/Salt3/Salt4 `corner_lower_right`. Each row keeps the same downstream-minus-upstream sign convention and preserves gross static rise, hydrostatic term, kinetic term, blocked straight/developing status, signed available residual, recirculation metrics, label, publication use, and admission status.

The allowed claims are that gross static pressure rises, that the rise is hydrostatic dominated, and that the signed available residual is section-effective pressure-recovery diagnostic evidence. The forbidden claims explicitly include negative loss, negative component K, F6 admission, hidden multiplier, and universal component-K closure.

## Inferred

The result is now paper-usable as a diagnostic finding. It is not coefficient-usable. The next scientific work should standardize pressure-plane basis and same-QOI UQ before any low-recirculation anchor or comparison/admission review.

## Contradictions Or Caveats

The freeze inherits the same blockers as the source audit: no same-basis straight/developing reference, no recovery diagnostics, material reverse flow, apparent-cluster-only isolation, and missing same-QOI UQ. The package intentionally does not resolve those blockers.

## Next Useful Actions

Run the next phases in this order: pressure-plane basis standardization, same-QOI UQ/recovery gate, matched-plane recirculation harvest, low-recirculation anchor harvest when terminal-gated source cases are available, then comparison/admission review.
