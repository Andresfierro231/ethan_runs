---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_fitting_source_page_geometry_recovery/facility_geometry_recovery.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest/matched_plane_recirc_field_harvest.csv
tags: [litrev-synthesis, signed-flow, junction, pressure-ledger]
related:
  - .agent/status/2026-07-21_TODO-LITREV-SIGNED-FLOW-JUNCTION-FEASIBILITY.md
  - imports/2026-07-21_litrev_signed_flow_junction_feasibility.json
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_signed_flow_junction_feasibility/README.md
task: TODO-LITREV-SIGNED-FLOW-JUNCTION-FEASIBILITY
date: 2026-07-21
role: Hydraulics/Writer/Reviewer
type: journal
status: complete
---
# LitRev Signed-Flow Junction Feasibility

## Attempted

Evaluated MF-03 signed-flow junction feasibility from current model-form,
source-inventory, fitting-geometry, recirculation, and single-stream gate
evidence.

## Observed

MF-03 requires a discrete modeled branch with net sign change, path pressure
reversal, topology consistency, signed path mass flows, and a source-bounded
velocity/pressure basis. The facility tee and `junction_other` rows lack exact
topology, branch numbering, physical pressure members, pressure nodes, and
signed path mdot. Current lower-right and test-section evidence indicates local
reverse-flow/section-effective behavior, not a three-node signed-flow network.

## Inferred

MF-03 should not be implemented from current evidence. Facility tee and
`junction_other` should stay deferred until geometry/topology mapping exists.
Local exchange and section-effective rows should stay in MF-04 or diagnostic
pressure lanes.

## Caveats

No network solver, source coefficient, tee Kprime, branch split fit, or model
selection was performed.

## Next Useful Actions

The next pressure-side progress path is same-QOI UQ and terminal-gated harvest,
not signed-flow implementation. Reconsider MF-03 only after a physical tee or
junction map proves a discrete branch changes net sign.
