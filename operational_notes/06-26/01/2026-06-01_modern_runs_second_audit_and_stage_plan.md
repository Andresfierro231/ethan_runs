# 2026-06-01 modern_runs second audit and stage plan

## Observed output

- A second readability audit was run after the external permission change had progressed.
- Current state:
  - all 8 salt cases are fully readable
  - all 4 water laminar cases are fully readable
  - all 4 water `kOmegaSSTLM` cases expose setup metadata but still do not expose
    `logs/log.foamRun` or `postProcessing/`
- The missing water `kOmegaSSTLM` outputs no longer look like a pure permission
  issue. At least one representative case shows top-level setup folders and prep
  logs such as `log.copyMesh` and `log.decomposePar`, but no solver-output tree.

## Interpretation

- The external `chmod` appears complete enough for intake planning.
- The remaining gap is case state, not broad source unreadability.
- The right first batch is now broader than the original snapshot: stage the 8
  salt cases and all 4 water laminar cases.
- Treat the 4 water `kOmegaSSTLM` cases as setup-only placeholders until solver
  outputs are generated or exported.

## Stage plan

- Local stage root:
  `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch`
- Provenance mapping:
  `jadyn_runs/modern_runs/2026-06-01_source_inventory/batch_manifests/first_batch_source_to_stage_map.json`
- Staging script:
  `jadyn_runs/modern_runs/2026-06-01_source_inventory/scripts/stage_first_batch.sh`
- Registration script:
  `jadyn_runs/modern_runs/2026-06-01_source_inventory/scripts/register_first_batch.sh`

## Deferred cases

- `val_water_test_1_coarse_mesh_kOmegaSSTLM`
- `val_water_test_2_coarse_mesh_kOmegaSSTLM`
- `val_water_test_3_coarse_mesh_kOmegaSSTLM`
- `val_water_test_4_coarse_mesh_kOmegaSSTLM`

These remain important for model-form comparison, but they are not yet
extractable validation runs in the current source state.
