---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release/topology_cv_case_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release/face_connected_component_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release/boundary_escape_by_patch.csv
tags: [journal, upcomer, exchange-cell, topology, recirculation, s13, no-admission]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-CV-RELEASE-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_topology_cv_release.json
task: TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-CV-RELEASE-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# S13 Upcomer Exchange Topology CV Release

## Attempted

Implemented and ran a topology pass that uses OpenFOAM `owner/neighbour` face
adjacency to relabel the Salt2/Salt3/Salt4 reverse-flow diagnostic masks into
face-connected components. The same mesh topology source was then used to
derive internal interface face counts/areas, trusted right-leg wall contact,
and boundary escape by patch for the largest face-connected component.

## Observed

The face-connected component structure is nearly identical to the earlier
point-connected largest-component result. The largest face-connected component
is about `53%` of reverse-flow candidates in each case. Each selected component
has a positive diagnostic internal interface area, but no contact with the
trusted `pipeleg_right_01_lower`, `pipeleg_right_02_middle`, or
`pipeleg_right_03_upper` wall patches.

The selected components instead contact lower-leg boundary patches. The largest
recurring escape is `pipeleg_lower_06_straight` with `4204` faces and
`0.00685491815391 m2` in all three cases.

## Inferred

The current reverse-flow mask is not a released recirculation control volume.
The topology evidence suggests the dominant reverse-flow region selected by
the right-leg ROI/velocity sign rule is not a closed right-leg exchange cell
against the trusted wall band. Using it for `mdot_exchange`, `Q_wall_W`, or
exchange-cell coefficients would mix regions and violate the source-geometry
contract.

## Contradictions Or Caveats

The diagnostic interface area is nonzero, so there is useful geometry for
method development. It is not a production exchange interface because the CV
itself fails the dominance, wall-contact, and boundary-escape gates.

Only one shared Salt2 continuation `constant/polyMesh` was used as the topology
source for Salt2/Salt3/Salt4, consistent with the shared cell counts and prior
cell VTK/volume manifests. A later release-grade row should either prove mesh
identity across all three native cases or stream each case's own `polyMesh`.

## Next Useful Actions

1. Audit the right-leg ROI definition against pipeleg patch extents and
   centroid envelopes; determine why the selected component contacts lower-leg
   patches.
2. Add a patch-aware segmentation stage that seeds or filters reverse-flow
   candidates by trusted right-leg wall adjacency before component release.
3. If a right-leg wall-adjacent component becomes dominant and boundary-closed,
   derive exchange-interface face sets and wall/core band from that component.
4. Keep exchange-cell harvest, `Q_wall_W`, same-window UQ execution, and
   coefficient fitting disabled until the geometry gates pass.
