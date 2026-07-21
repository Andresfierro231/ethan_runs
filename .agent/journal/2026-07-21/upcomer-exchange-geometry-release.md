---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/geometry_release_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/cell_vtk_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/facezone_candidate_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/wall_core_candidate_audit.csv
tags: [journal, upcomer, exchange-cell, geometry-release, cell-vtk, no-solver]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-GEOMETRY-RELEASE-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_geometry_release.json
task: TODO-UPCOMER-EXCHANGE-GEOMETRY-RELEASE-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Geometry Release

## Attempted

Advanced the recommended sequence by separating geometry release from scheduler
execution. The work audited the existing cell-volume package, surface/source
package, reusable sampler scaffold, native `topoSetDict` faceZones, and mesh
centerline station packages to decide which extraction lanes can proceed.

## Observed

The prior cell-volume generation produced ready Salt2/Salt3/Salt4 volume CSVs
with `2166996` cells each. Whole-mesh cell VTK extraction can preserve direct
cell ordering without inventing an upcomer cellSet, so it is releasable for a
separate scheduler row if that row verifies VTK cell count and `U`, `T`, `rho`
field presence.

The native `topoSetDict` files define `mdot_pipeleg_*` plane faceZones. These
are loop section mass-flow planes, not a conservative interface separating the
main throughflow from a recirculation cell. The surface/source package also
listed `upcomer_outlet_proxy`, but that is a representative proxy and is not
adequate for exchange-interface accounting.

Mesh station packages identify wall patch spans, including the right/upcomer
leg, but they do not define a recirculation cell region or wall/core band.

## Inferred

The rigorous next action is to run only whole-mesh cell VTK extraction under a
new scheduler-owned row. The exchange-interface and wall/core lanes should stay
blocked until they have physically owned region definitions. Using the existing
mass-flow planes or upcomer outlet proxy would collapse different heat paths
and risk hiding the residual in internal `Nu`.

## Contradictions Or Caveats

Whole-mesh VTK is larger than a targeted cellSet extraction, but it avoids a
premature region definition and is safer for cell-volume alignment. It does not
solve the exchange-interface or wall/core definitions by itself; it only unlocks
the field snapshot lane needed by the sampler.

## Next Useful Actions

1. Claim a scheduler row for `whole_mesh_cell_vtk_extraction`.
2. Stage task-local Salt2/Salt3/Salt4 continuation cases and extract whole-mesh
   `U`, `T`, and `rho` cell VTKs for the already selected time windows.
3. Verify each VTK has `2166996` cells and fields `U`, `T`, and `rho`; record
   any ordering or cellId evidence before sampler use.
4. In a separate geometry row, define the conservative main/recirculation
   exchange interface with point, normal, area/sign convention, and provenance.
5. In a separate wall/core row, define the recirculation cell region and
   wall/core band before wallHeatFlux integration or residual accounting.
