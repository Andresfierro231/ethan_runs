# 2026-06-01 modern_runs source inventory

This folder records the first heavy documentation pass for
`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs`.

## Snapshot scope

- Source tree only. No solver outputs were modified.
- Inventory timestamp: `2026-06-01T11:46:33-05:00`.
- Permission state is transitional because a long-running `chmod` operation was
  reportedly still in progress during this pass.

## High-level findings

- `salt/` is a coherent viscosity-screening campaign with 8 readable cases.
- `water/` is a validation/turbulence campaign with 8 named cases, but source
  readability is uneven in this snapshot.
- Common readable metadata across accessible cases:
  - `mesh_group_id = 7ab7fb2650596980`
  - `nprocs = 64`
  - `walltime = 120:00:00`
  - `scale_to_meters = 0.001`
  - `ncc_couples = 10`
  - convergence enabled with `check_interval = 100`, `min_iterations = 500`,
    QoI `rtol = 1e-4`, window `100`

## Readability classes

- `full_extractable`: readable `case_config.yaml`, `system/controlDict`,
  `logs/log.foamRun`, `postProcessing`, and `constant/polyMesh/boundary`
- `partial_extractable`: readable run metadata and outputs, but missing at
  least one geometry/setup artifact
- `partial_metadata`: readable setup metadata only; solver outputs are still
  blocked
- `blocked`: not readable enough yet for dependable local extraction

## Recommended staging order

1. Stage the 8 salt cases first. They are the cleanest complete batch and give
   immediate leverage for cross-viscosity comparisons.
2. Stage `val_water_test_1_coarse_mesh_laminar` and
   `val_water_test_2_coarse_mesh_laminar` next. They appear fully extractable
   in this snapshot.
3. Recheck permissions for `val_water_test_4_coarse_mesh_laminar`,
   `val_water_test_2_coarse_mesh_kOmegaSSTLM`, and
   `val_water_test_3_coarse_mesh_kOmegaSSTLM` before registration.
4. Hold the remaining blocked water cases until the permission pass finishes,
   then rerun this inventory before any staging decision.
