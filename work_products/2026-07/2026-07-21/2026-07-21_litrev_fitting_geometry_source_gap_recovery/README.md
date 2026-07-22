---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_fitting_inventory_source_envelope/fitting_inventory.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_cfd_postprocessing_schema_gap/cfd_postprocessing_schema_gap_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv
tags: [litrev-synthesis, minor-loss, source-envelope, geometry, pressure-ledger]
related:
  - .agent/status/2026-07-21_TODO-LITREV-FITTING-GEOMETRY-SOURCE-GAP-RECOVERY.md
  - .agent/journal/2026-07-21/litrev-fitting-geometry-source-gap-recovery.md
task: TODO-LITREV-FITTING-GEOMETRY-SOURCE-GAP-RECOVERY
date: 2026-07-21
role: Implementer/Writer
type: work_product
status: complete
---
# LitRev Fitting Geometry Source Gap Recovery

## Decision

The 1D fittings path can progress by recovering geometry and source-page gaps,
not by importing coefficients. The current source-envelope package already
identifies every relevant fitting/cluster row; this package converts those rows
into physical-location, geometry-dimension, pressure-basis, source-page, and
model-lane next actions.

## Outputs

- `geometry_source_gap_recovery.csv`: 10 fitting/cluster recovery rows.
- `fitting_physical_location_map.csv`: 10 physical location rows.
- `source_page_audit_queue.csv`: 5 source-family audit rows.
- `source_manifest.csv`, `summary.json`, package builder, and test.

## Current Interpretation

- `corner_lower_right` is now downstream of the completed pressure-corner audit:
  current Salt2-Salt4 endpoint rows are `section_effective`, not component or
  cluster coefficients.
- Quartz lower/upper transitions have useful diameter evidence but still lack
  transition length, reducer/expansion angle, edge radius, pressure bracketing,
  and source-page mapping.
- The heat-exchanger reducer and tee/corner facility fitting are source-gap
  rows until facility part/location evidence is mapped to the CFD geometry.
- `junction_other` remains a thermal patch group and cannot become a pressure
  fitting row until the physical members and pressure planes are identified.
- `test_section_complex` stays in the throughflow-plus-recirculation/exchange
  lane unless future evidence isolates component boundaries and low-reverse
  throughflow.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state, Fluid
source, external repo files, source coefficients, F6 fit, component coefficient,
global multiplier, clipped sign, or unlabeled numeric fitting term were changed
or introduced.
