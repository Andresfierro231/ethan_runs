---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/same_qoi_uq_admission_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/uq_gap_queue.csv
tags: [pressure-corner, same-qoi-uq, scientific-synthesis, publication-claims]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/pressure_corner_methods_note.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/README.md
task: TODO-PRESSURE-CORNER-SAME-QOI-SCIENTIFIC-SYNTHESIS-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer/Tester
type: work_product
status: complete
---
# Scientific Finding Narrative

## Finding

The current Salt2/Salt3/Salt4 `corner_lower_right` candidates show a gross
static pressure rise across `lower_leg__s04->right_leg__s00`, but the rise is
hydrostatic dominated. Across the three frozen rows, gross static rise spans
3035.1 to 3068.72 Pa and the hydrostatic fraction of gross
spans 1.00043 to 1.00063. After hydrostatic and
kinetic correction, the signed available residual remains negative
(-1.84957 to -1.25367 Pa).

## What Worked

The sign-safe decomposition worked. The result can be compared, plotted, and
written scientifically as a section-effective pressure residual plus
pressure-recovery diagnostic. The same-QOI UQ package also worked as a
cross-family status ledger: 83 rows now carry same-label,
same-formula, same-sign, basis, window, mesh/GCI, plane-sweep, and final-use
status.

## What Did Not Work

No row became an admitted coefficient. The same-QOI table has
0 admitted rows, 0
component-K rows, 0 cluster-K rows,
0 F6-fit rows, 0
clipped-K rows, and 0
package-applied global-multiplier rows.

The reason is physical and methodological, not just clerical: the current
corner section materially recirculates, component isolation is only
apparent-cluster-level, the straight/developing reference is missing on the
same basis, and same-QOI neighboring-window plus mesh/GCI evidence is missing.

## Efficient Continuation

Continue in this order:

1. Claim the low-recirculation anchor harvest row and preflight terminal/source
   paths before any sampler launch.
2. Inventory same-QOI neighboring windows and mesh/GCI availability for the
   three current corner residual rows.
3. Claim a raw F6 endpoint face sampler row for the six clean endpoint pairs
   and twenty face targets.
4. Run comparison/admission review only after new evidence lands.
5. Write the paper-facing section from the frozen diagnostic result or from the
   later comparison package.

## Forbidden Interpretations

Do not call the signed residual a negative loss. Do not clip it into a positive
K. Do not use it as component-K, cluster-K fit, or F6 input. Do not hide it
inside a global multiplier. Those actions would erase the physical content of
the hydrostatic/recovery decomposition and violate the same-QOI uncertainty
status.
