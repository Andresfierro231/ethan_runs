---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/litrev_source_inventory.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - reference/geometry_reference.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_fitting_inventory_source_envelope/fitting_inventory.csv
tags: [litrev-synthesis, minor-loss, source-envelope, pressure-ledger, geometry]
related:
  - .agent/status/2026-07-21_TODO-LITREV-FITTING-INVENTORY-SOURCE-ENVELOPE.md
  - imports/2026-07-21_litrev_fitting_inventory_source_envelope.json
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_fitting_inventory_source_envelope/README.md
task: TODO-LITREV-FITTING-INVENTORY-SOURCE-ENVELOPE
date: 2026-07-21
role: Implementer/Writer
type: journal
status: complete
---
# LitRev Fitting Inventory Source Envelope

Task: TODO-LITREV-FITTING-INVENTORY-SOURCE-ENVELOPE

## Attempted

Built an inventory-only source-envelope package for TAMU local pressure-loss
features implied by the new LitRev. The goal was to identify what can accept a
future source-bounded pressure-loss term, not to score or admit a coefficient.

## Observed

The requested LitRev extraction package requires pressure basis, velocity basis,
hydrostatic correction, kinetic correction, straight/developing subtraction,
component/cluster classification, recovery status, recirculation metrics, and
same-QOI uncertainty before any local coefficient can be admitted.

The current repo evidence provides strong geometry/span labels for the six
primary CFD spans and four loop corners. It also identifies the test-section
bore as 20.9 mm against 30 mm neighboring upcomer sections, making two quartz
area-change transitions real inventory items. Current pressure packages already
preserve four corner names and `test_section_complex`, but they keep those rows
diagnostic or section-effective. `corner_lower_right` has the best endpoint
pressure/velocity evidence, yet current rows have material reverse flow,
apparent-cluster classification, and missing same-QOI UQ.

The LitRev/facility source reports a heat-exchanger reducer and tee/corner
fitting, but the current Ethan geometry reference and pressure products do not
locate pressure-isolated rows for those features. The `junction_other` label is
currently a thermal patch group, not a pressure-loss coefficient basis.

## Inferred

The correct next modeling posture is to keep the four corners and
test-section/quartz assembly as section, cluster, or recirculation-lane
candidates until geometry and basis fields are proven. Reducer, expansion, and
tee source families are useful for source-envelope requirements and future
schemas, but not for importing numerical K values today.

The rows most likely to need future work are split into three classes:
pressure-basis/component-isolation gates for ordinary corners, geometry source
gaps for reducers/quartz transitions/tee features, and recirculation or
exchange-cell gates for the upcomer/test-section complex and current
`corner_lower_right` endpoint evidence.

## Caveats

The inventory uses current repository evidence and the LitRev source audit. It
does not read native CFD outputs, launch extraction, inspect CAD/manufacturer
part pages, or update registry/admission state. Some facility-reported features
are necessarily rows with unresolved location and geometry because the source
evidence says they exist but current pressure artifacts do not bracket them.

## Next Useful Actions

Use `inventory_gap_queue.csv` as the handoff. The highest-leverage follow-ons
are: recover facility/CAD part geometry for reducer and tee rows; keep
`corner_lower_right` in the recirculating section-effective lane unless a
low-reverse same-topology anchor lands; and require same-QOI mesh/time UQ before
any component or cluster K review.
