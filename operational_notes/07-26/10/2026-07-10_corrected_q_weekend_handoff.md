# 2026-07-10 Corrected-Q Weekend Handoff

## Running Jobs

- `3282992` Salt1 nominal: still running on `c318-016`; excluded until terminal
  admission evidence exists.
- `3288671` selected corrected-Q packed continuation: running on `c318-017`.
  Live solver steps at final check:
  - `3288671.0`: Salt1 -10Q corrected.
  - `3288671.1`: Salt1 +10Q corrected.
  - `3288671.5`: repaired Salt4 +10Q corrected.

## Salt4 +10Q Repair State

Salt4 +10Q corrected is now attached as `3288671.5` and had advanced to latest
written timestep `11537.000 s` / latest log time `11537.723 s` at final table
regeneration. It has passed the earlier
OpenFOAM time-precision failure point `11536.488262910847`.

Monitor:

```bash
sacct -j 3288671 --format=JobID,JobName,State,Elapsed,AllocCPUS,NTasks,NNodes,NodeList,ExitCode
tail -120 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_salt4_hi10q_weekend_attach
tmux ls
```

Do not submit or attach another Salt4 +10Q attempt unless `3288671.5` fails.

## Latest-Time Product

Use:

```bash
python3.11 tools/analyze/build_registry_corrected_q_status_table.py --strict-registry
```

Primary output:

`work_products/2026-07/2026-07-10/2026-07-10_registry_corrected_q_status_table/corrected_q_latest_timesteps.csv`

This table reports every registered corrected-Q row's gate latest time, latest
written case timestep, and latest parsed log time.

## Admission Boundary

Corrected-Q rows remain sensitivity/correlation-support. Do not move Salt1
corrected rows or Salt4 +10Q corrected into closure fits without post-run gate
evidence.
