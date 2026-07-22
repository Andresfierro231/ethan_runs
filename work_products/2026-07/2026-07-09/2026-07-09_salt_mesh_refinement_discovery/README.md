# Salt Mesh Refinement Discovery

Generated: `2026-07-09`

## Scope

This is a read-only discovery pass over Ethan's Salt mesh-family drop at:

`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt/`

No solver outputs were modified, copied, registered, staged, or postprocessed in
this pass.

## Observed Structure

The source tree contains three mesh levels:

- `coarse/`: 8 Salt cases, `processors64`, `2,166,996` cells.
- `medium/`: 8 Salt cases, `processors64`, `6,744,264` cells.
- `fine/`: 8 Salt cases, `processors128`, `21,781,672` cells. This is the
  "highly refined" level in the user's request.

Each level contains Salt tests `1-4`, each with `jin` and `kirst` property
variants. Each case has `case_config.yaml`, `system/`, `constant/`, `0/`,
`postProcessing/`, `dynamicCode/`, `logs/`, and a collated processor directory.
The postProcessing families are consistent across sampled cases:

`piv_slab_velocity`, `temperature_probes`, `wall_temperature_probes`,
`velocity_profiles`, `wallShearStress`, `wallHeatFlux`, `yPlus`,
`total_Q.dat`, and four `mdot_pipeleg_*` channels.

## Key Findings

- Permissions are now sufficient for inventory. On July 7, prior notes said the
  mesh folders existed but denied traversal.
- Mesh refinement is regular enough for a GCI attempt: cell counts increase
  `2,166,996 -> 6,744,264 -> 21,781,672`, about `3.1x` per level.
- Mesh settings from `case_config.yaml` are:
  - coarse: `first_cell_size=0.225`, `bulk_cell_size=1.125`,
    `mesh_group_id=7ab7fb2650596980`;
  - medium: `first_cell_size=0.15`, `bulk_cell_size=0.75`,
    `mesh_group_id=d9a216dc1a1a0424`;
  - fine: `first_cell_size=0.1`, `bulk_cell_size=0.5`,
    `mesh_group_id=8cbc7f2f3d28cbeb`.
- Most medium/fine runs ended by signal 15 at allocation shutdown rather than
  reaching a clean `End`. Salt 2 Jin is the strongest immediate mesh-family
  candidate because both medium and fine tails report `convergenceMonitor:
  CONVERGED` and clean termination.
- Salt 4 Jin is still important as the high-Re endpoint requested by the prior
  GCI protocol, but its medium/fine logs tail with signal 15 and need a quality
  gate before any GCI or closure admission.
- Kirst rows are inventoried for provenance only. Repo policy still treats
  Kirst as historical unless a later dated task explicitly re-admits it.

## Files

- `mesh_case_inventory.csv`: case-level inventory with exact paths, mesh level,
  case id, cell count, processor layout, latest times, log-tail status, and
  initial admission priority.

## Immediate Admission Recommendation

Do not update `registry/case_registry.csv` or `closure_observations.csv` directly
from this discovery package. Next pass should first stage or formally register
the mesh-family source paths, then run lightweight quality checks:

1. Reconcile external `coarse/` cases against the existing repo mainline
   continuation cases. The source tree's coarse logs are May 28 warmup-era files,
   while repo policy says continuation runs are the current mainline when they
   exist.
2. Start the GCI readiness pass with Salt 2 Jin at coarse/medium/fine because
   medium and fine are cleanly converged in the inspected log tails.
3. Evaluate Salt 4 Jin next as the upper endpoint, but expect continuation or a
   stricter steadiness check before using it as closure evidence.
4. Keep Salt 1/3 Jin as secondary coverage and Kirst as historical provenance.
5. Only after GCI readiness passes should mesh uncertainty be propagated into
   the July 8 `closure_observations.csv` contract.

## Prior Context Used

- `operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md`
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`
- `work_products/2026-07/2026-07-08/2026-07-08_closure_observation_table/README.md`
