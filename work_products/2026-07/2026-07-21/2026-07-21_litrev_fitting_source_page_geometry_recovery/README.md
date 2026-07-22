---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_fitting_geometry_source_gap_recovery/geometry_source_gap_recovery.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_fitting_geometry_source_gap_recovery/source_page_audit_queue.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/pressure_plane_basis_standardization.csv
tags: [litrev-synthesis, source-envelope, geometry, minor-loss]
related:
  - .agent/status/2026-07-21_TODO-LITREV-FITTING-SOURCE-PAGE-GEOMETRY-RECOVERY.md
  - .agent/journal/2026-07-21/litrev-fitting-source-page-geometry-recovery.md
task: TODO-LITREV-FITTING-SOURCE-PAGE-GEOMETRY-RECOVERY
date: 2026-07-21
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# LitRev Fitting Source-Page Geometry Recovery

This package turns the fitting geometry/source-gap inventory into a source-page
and facility-geometry recovery ledger. It is not a coefficient table.

## Outputs

- `facility_geometry_recovery.csv`: 10 feature rows.
- `source_equation_validity_queue.csv`: 5 source-family rows.
- `feature_geometry_blockers.csv`: 10 feature blocker rows.
- `source_manifest.csv`, `summary.json`, builder, and package test.

## Main Findings

- Quartz transition source review is blocked by transition length, angle, edge
  radius, pressure bracketing, straight reference, and recirculation treatment.
- The heat-exchanger reducer and tee/corner rows are facility-geometry rows
  until part/location evidence maps to current geometry or CFD patch/span labels.
- Loop corners still need bend radius or miter data, component boundaries,
  recovery length, tap sweep, pressure/velocity basis, and same-QOI UQ.
- `junction_other` remains a thermal patch group until physical pressure
  fitting members and pressure planes are mapped.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
solver/postprocessing launch, Fluid/external files, source coefficients,
component K, cluster K, F6 fit, global multiplier, or clipped sign were changed
or introduced.
