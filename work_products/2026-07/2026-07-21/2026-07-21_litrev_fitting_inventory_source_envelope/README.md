---
task: TODO-LITREV-FITTING-INVENTORY-SOURCE-ENVELOPE
date: 2026-07-21
role: Implementer / Writer
type: work_product
status: complete
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - reference/geometry_reference.md
  - operational_notes/maps/pressure-and-momentum-budget.md
tags: [litrev-synthesis, minor-loss, pressure-ledger, source-envelope, geometry]
related:
  - .agent/status/2026-07-21_TODO-LITREV-FITTING-INVENTORY-SOURCE-ENVELOPE.md
  - .agent/journal/2026-07-21/litrev-fitting-inventory-source-envelope.md
---
# LitRev Fitting Inventory Source Envelope

## Why this package exists
This package inventories loop features that could receive a source-bounded local
pressure-loss term under the LitRev minor-loss rules. It is intentionally
conservative: every row is an inventory/admission-gate row, not an admitted
coefficient row.

## Outputs
- `fitting_inventory.csv` has 10 fitting, junction, reducer, tee, quartz-transition, and cluster rows.
- `source_envelope_status.csv` has 9 source-family rows describing usable evidence and hard limits.
- `inventory_gap_queue.csv` turns each inventory row into a next-evidence item.
- `source_manifest.csv` records read-only context and mutation flags.
- `summary.json` records counts and guardrails.

## Current Findings
- The four loop corners have geometry/span evidence and diagnostic apparent or
  upper-bound pressure evidence, but no row has component isolation, recovery,
  final pressure/velocity basis, recirculation gates, and same-QOI UQ together.
- `corner_lower_right` is the best documented pressure feature, but current
  endpoint evidence is material-reverse-flow section evidence, not an ordinary
  component K.
- The quartz/test-section area changes are real geometry features, but exact
  transition dimensions and coefficient sources remain unresolved. They belong
  in `test_section_complex` unless future evidence isolates components.
- The LitRev/facility source reports a heat-exchanger reducer and tee/corner
  fitting, but current repo evidence does not locate pressure-isolated rows for
  those features. They remain source-gap inventory items.
- `junction_other` currently has thermal patch evidence, not pressure-loss
  coefficient evidence.

## Admission Policy
No numerical K value is admitted in this package. Rows that mention prior K-like
evidence carry only diagnostic labels such as `apparent_upper_bound_diagnostic`,
`section_effective`, `cluster_residual`, or `source_gap`. Future coefficient work
must prove geometry match, pressure basis, velocity basis, straight/developing
subtraction, recovery, recirculation status, and same-QOI uncertainty first.

## Guardrails
- No native CFD/OpenFOAM output was changed.
- No registry or admission state was changed.
- No scheduler or postprocessing job was launched.
- No Fluid or external source-tree file was edited.
- No F6 fit, component K, global multiplier, clipped K, or unlabeled K was admitted.
