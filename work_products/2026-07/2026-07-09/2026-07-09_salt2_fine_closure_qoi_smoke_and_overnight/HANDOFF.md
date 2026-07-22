# AGENT-239 Handoff

Updated: `2026-07-09T17:18:00-05:00`

## What Happened

This task prepared and ran Salt2 Jin refined-mesh closure-QOI extraction for:

- medium mesh: source time `518`, source processors `processors64`
- fine mesh: source time `399`, source processors `processors128`

The source case trees under
`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt/`
were not modified. The runner stages local reconstruction mirrors under this
package, symlinks source processor/monitor data, and writes all derived products
under `outputs/`.

## Important Correction

The first implementation used `tmux+srun` from the interactive allocation. That
was not the right overnight execution path. The run finished quickly anyway
before the correction was requested:

- medium started `2026-07-09T16:40:16-05:00`
- medium completed `2026-07-09T16:44:14-05:00`
- fine started `2026-07-09T16:44:14-05:00`
- fine completed `2026-07-09T16:58:31-05:00`

No process remains running in the interactive allocation.

## Scheduled Batch Path

An `sbatch` wrapper now exists:

`scripts/sbatch_smoke_then_overnight_10pm.sh`

It is configured for:

- account: `ASC23046`
- partition: `NuclearEnergy`
- nodes/tasks/threads: `-N 1 -n 1 -c 128`
- walltime: `08:00:00`
- begin time: `2026-07-09T22:00:00`

Expected submit command from a login node:

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
sbatch work_products/2026-07/2026-07-09/2026-07-09_salt2_fine_closure_qoi_smoke_and_overnight/scripts/sbatch_smoke_then_overnight_10pm.sh
```

Job `3287480` was submitted for `2026-07-09T22:00:00`, then cancelled after the
user clarified that no rerun is needed if the interactive medium/fine extraction
already completed. The cancelled batch would have rerun the same
`smoke_then_overnight` driver and would not have produced a new analysis stage.

## Outputs Already Present

Medium outputs:

- `outputs/medium/section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.{json,csv}`
- `outputs/medium/segment_friction.{json,csv}`
- `outputs/medium/momentum_budget.{json,csv}`
- `outputs/medium/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.{json,csv}`
- `outputs/medium/run_provenance.json`

Fine outputs:

- `outputs/fine/section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.{json,csv}`
- `outputs/fine/segment_friction.{json,csv}`
- `outputs/fine/momentum_budget.{json,csv}`
- `outputs/fine/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.{json,csv}`
- `outputs/fine/run_provenance.json`

## Profile Mapping Caveat

The physical source cases are medium/fine, but the station/segment profile
source ID is `viscosity_screening_salt_test_2_jin_coarse_mesh`. This is
intentional: refined Salt2 source IDs are not registered in
`tools.case_analysis_profiles`, so the coarse Salt2 Jin profile is used only as
the station/segment contract. Physical mesh provenance is carried in
`sampling_targets.csv` and each `run_provenance.json`.

## Next Fresh-Agent Checks

1. Confirm job `3287480` remains cancelled/absent from `squeue`; no 10pm rerun
   is expected.
2. Run row-level sanity checks on medium/fine closure-QOI values before any GCI.
3. Compare mainline coarse, external medium, and external fine closure QoIs.
4. Only after a closure-QOI mesh-UQ table is reviewed should
   `closure_observations.csv` be considered for update.
