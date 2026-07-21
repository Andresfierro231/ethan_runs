# Mesh Refinement Discovery Plan

Date: `2026-07-09`
Role: `Coordinator / Writer`
Task ID: `AGENT-226`
Branch/worktree: current workspace

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `README.md`
- `jadyn_runs/modern_runs/README.md`
- `operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md`
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`
- `work_products/2026-07/2026-07-08/2026-07-08_closure_observation_table/README.md`
- Ethan source tree under `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt/`

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-09_AGENT-226.md`
- `.agent/journal/2026-07-09/mesh-refinement-discovery-plan.md`
- `imports/2026-07-09_salt_mesh_refinement_discovery.json`
- `operational_notes/07-26/09/2026-07-09_salt_mesh_refinement_discovery_plan.md`
- `work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_discovery/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_discovery/mesh_case_inventory.csv`

## Commands Run

- `find` over the source tree for mesh levels, case directories, lightweight
  config/log files, postProcessing families, and processor directories.
- `rg` over recent journals/notes/imports/work products for mesh/GCI and
  closure-observation context.
- `tail` and `rg` on representative and per-case `logs/log.foamRun` files.
- `rg` on `case_config.yaml`, `system/controlDict`, and `logs/log.decomposePar`
  for mesh settings, processor layout, control settings, and cell counts.

## Observations

- Source visibility is now unblocked. Prior July 7 notes recorded the same
  coarse/medium/fine folders but said traversal was denied.
- All `24` Salt mesh-family cases are present.
- Mesh levels are consistent by cell count and case config:
  `coarse=2,166,996`, `medium=6,744,264`, `fine=21,781,672`.
- `fine` uses `processors128`; `coarse` and `medium` use `processors64`.
- Processor folders are collated time-directory layouts, not `processor0...`
  directory layouts.
- Salt 2 Jin medium and fine show clean convergence monitor completion in log
  tails. Most other medium/fine runs tail with signal 15 termination, likely
  walltime shutdown, and need quality gating before use.
- No GCI or closure-correlation retry was performed in this pass.

## Incomplete Lines Of Investigation

- Need to reconcile external `coarse/` roots with repo mainline continuation
  roots before treating them as the coarse level for GCI.
- Need scripted quality gate for mdot drift, heat-duty drift, y+, required field
  presence, and postProcessing completeness.
- Need a staged/intake manifest if future tasks copy or register source data.
- Need GCI calculation only after per-QOI monotonicity/asymptotic checks.

## Next Steps

1. Open a new board row for a script-driven quality gate and manifest builder.
2. Start with Salt 2 Jin mesh family, then Salt 4 Jin endpoint.
3. Propagate accepted mesh uncertainty into `closure_observations.csv` before
   any closure-correlation refit.
