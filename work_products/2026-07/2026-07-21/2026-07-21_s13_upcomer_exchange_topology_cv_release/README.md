---
task: TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-CV-RELEASE-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_fail_closed_topology
tags: [upcomer, exchange-cell, topology, control-volume, fail-closed]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight
  - work_products/2026-07/2026-07-21/2026-07-21_candidate_uq_s13_geometry_recovery
---
# S13 Upcomer Exchange Topology Control-Volume Release

This package uses the completed right-leg reverse-flow diagnostic masks and
OpenFOAM owner/neighbour topology to decide whether a face-connected
recirculation control volume can release the S13 exchange-interface and wall
lanes.

## Decision

- cases processed: `3`
- topology CV rows released: `0`
- exchange-interface rows released: `0`
- wall/core rows released: `0`
- surface extraction allowed: `false`
- scheduler action: `false`
- sampler/harvest launched: `false`

The topology pass relabels the right-leg reverse-flow candidates into
face-connected components from OpenFOAM `owner/neighbour`, then derives
interface and wall face counts/areas for the largest face-connected component.
It still fails closed unless the same physical topology source yields a
dominant component, positive interface area, positive trusted wall-band area,
and no unclassified boundary escape. Therefore this package does not release
`exchange_interface_vtk`, `wall_vtk`, or `Q_wall_W` unless those gates all pass
for Salt2/Salt3/Salt4 together.

## Outputs

- `topology_cv_case_summary.csv`
- `face_connected_component_summary.csv`
- `boundary_escape_by_patch.csv`
- `masks/*_selected_face_connected_recirc_cv_mask.csv`
- `exchange_interface_topology_contract.csv`
- `wall_core_topology_contract.csv`
- `downstream_surface_extraction_gate.csv`
- `no_mutation_guardrails.csv`, `source_manifest.csv`, and `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated docs index, surface
VTK extraction, sampler/harvest, fit, score, model selection, S11/S15/S6
trigger, or internal-Nu residual absorption is changed by this package.
