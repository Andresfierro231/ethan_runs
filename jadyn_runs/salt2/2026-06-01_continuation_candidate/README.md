# 2026-06-01 Continuation Candidate

Source case:
`/scratch/09748/andresfierro231/projects_scratch/val_salt_test_2_coarse_mesh_laminar`

Reason this folder exists:
- the imported source run stopped at about `1724.714285714 s`
- the configured `endTime` is `10000`
- the run does not satisfy the stated QoI convergence target for mdot and heat-loss metrics

Intended use:
- stage a writable copy here before any continuation or restart work
- preserve the imported source as read-only provenance
- keep continuation-specific scripts, logs, and notes local to this folder

Expected next action:
- run `scripts/stage_source_case.sh` to copy the source case into `case_stage/`
- only after staging, decide the exact continuation controls and submission script
