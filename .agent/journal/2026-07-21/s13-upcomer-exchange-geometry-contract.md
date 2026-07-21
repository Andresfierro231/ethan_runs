---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/interface_geometry_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/wall_core_band_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/downstream_surface_vtk_inputs.csv
tags: [journal, upcomer, exchange-cell, geometry-contract, fail-closed]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-GEOMETRY-CONTRACT-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_geometry_contract.json
task: TODO-S13-UPCOMER-EXCHANGE-GEOMETRY-CONTRACT-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# S13 Upcomer Exchange Geometry Contract

## Attempted

Converted the prior geometry-release audit into a downstream contract for S13:
per-case source ledger, interface normal-vector convention, wall/core band
contract, and surface/harvest input matrix.

## Observed

The audited `mdot_*` faceZones are section mass-flow planes. They do not define
a closed interface between main throughflow and a recirculation cell. The
representative upcomer outlet proxy is also explicitly rejected as an exchange
surface substitute.

Mesh centerline wall spans identify plausible right-leg/upcomer wall patches,
but no source defines the recirculation cell volume, the interface between that
volume and throughflow, or the wall/core band bounds. Static source/sink ledgers
exist, but they are not same-window wall heat flow over a released
recirculation wall band.

## Inferred

The next blocker is not cell-field availability. Salt2/Salt3/Salt4 whole-mesh
cell VTKs are available or validated, but the physical control-volume geometry
needed for `mdot_exchange`, `T_recirc`, and `Q_wall_W` is not trusted. Running a
sampler now would encode a proxy geometry as if it were a physical interface.

## Contradictions Or Caveats

The contract defines a future sign convention for `mdot_exchange`, but that is
not a release of an interface. It is only a convention to prevent ambiguity when
a trusted interface is later supplied.

## Next Useful Actions

1. Derive a recirculation control volume from velocity-field topology, labeled
   cell sets, or a trusted geometry source, and record its provenance.
2. From that volume, define the internal exchange surface and wall/core band
   with normals, area/face counts, and cell/face identity.
3. Only then claim the surface VTK extraction row and populate the sampler
   manifest.
