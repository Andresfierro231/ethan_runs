---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/pressure_corner_comparison_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/pressure_corner_gate_review.csv
tags: [pressure-ledger, minor-loss, source-envelope, recirculation]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-CORNER-COMPARISON-ADMISSION-REVIEW.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/README.md
task: TODO-PRESSURE-CORNER-COMPARISON-ADMISSION-REVIEW
date: 2026-07-21
role: Hydraulics / Reviewer / Tester / Writer
type: journal
status: complete
---

# Pressure Corner Comparison Admission Review

## Attempted

I compared the pressure-corner publication freeze to the later pressure-plane
basis standardization, same-QOI UQ execution, matched-plane recirculation
harvest, fitting geometry/source-gap recovery, and source-page recovery
packages. I built a small reproducible package that preserves the frozen rows
and adds gate-by-gate labels for the component-`K` decision.

## Observed

The frozen rows cover three current `corner_lower_right` cases. All three show
gross static pressure rise, hydrostatic fraction slightly above 1, negative
available residual after corrections, reverse-area fraction near `0.763`, and
reverse-mass fraction near `0.5`. Later same-QOI evidence keeps the pressure
formula/sign/basis diagnostic rows but fails or blocks q-ref, neighboring
window, mesh/GCI, plane sweep, recirculation, and same-QOI uncertainty gates.
The fitting geometry/source package keeps the lower-right corner at
`no_coefficient_admission`.

## Inferred

The later evidence strengthens the frozen interpretation rather than changing
it. The rows are useful for section-effective pressure recovery and
recirculating residual discussion, but they are not ordinary single-stream
component-loss evidence. Because the residual is negative, clipping or
sign-flipping it into a positive `K` would be an unsupported model-selection
step.

## Contradictions Or Caveats

The pressure basis is good enough for the diagnostic decomposition but not
enough for coefficient use. Component isolation and source-envelope geometry
remain incomplete. The source-family rows cite screening literature and
source-envelope requirements, not TAMU-matched coefficient pages.

## Next Useful Actions

Harvest a nonrecirculating same-topology anchor before reopening ordinary
component-`K` review. Complete same-QOI time/mesh uncertainty for the exact
pressure residual. Recover bend radius, part/source-envelope fields, and
recovery length for the lower-right corner. Keep F6 endpoint evidence separate.
