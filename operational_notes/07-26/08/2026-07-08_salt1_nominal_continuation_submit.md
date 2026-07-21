# Salt 1 Nominal Continuation Submit

Date: `2026-07-08`
Task: `AGENT-206`

## Answer

The June 25 Salt 1 base-continuation candidate was not corrected for a new long
continuation launch as-is. Its copied `system/functions` convergence monitor
still called `stopAt(writeNow)`, which is why the source tree ended at
`4026.15625 s`.

For this submit, a new isolated campaign was staged:

`jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate`

The staged copy keeps the nominal Salt 1 operating point and `endTime 10000`,
but changes the convergence monitor to diagnostic-only, matching the corrected
Salt-Q pattern. It logs when the criterion is met and continues to configured
`endTime`.

## Source And Target

Source:

`jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt1_jin_basecont/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation`

Target:

`jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation`

The target `SOURCE_PROCESSORS64.txt` points at the June 25 source tree's
`processors64`, so the job starts from the `4026.15625 s` retained state.

## Submitted Job

| Field | Value |
| --- | --- |
| Job ID | `3282992` |
| Job name | `salt1_nom_cont` |
| Partition | `NuclearEnergy` |
| Account | `ASC23046` |
| Nodes / ranks | `1` node, `64` ranks |
| Walltime | `120:00:00` |
| Submit host | `login3.ls6.tacc.utexas.edu` |
| Initial state | `PENDING (Priority)` |

Direct `sbatch` from the current shell was blocked because the shell is on a
compute node; the actual submission was made through `login3`.

## Pairing Caveat

This job cannot be packed with later-identified cases after it starts. It is a
single 64-rank continuation job. Any additional cases should be submitted as
separate jobs or staged into a separate packed allocation.

## Current Surrounding Queue

At submission check:

- `3275448 corr_saltq_g1`: running
- `3275449 corr_saltq_g2`: running
- `3275560 corr_saltq_salt4_all`: running
- `3280969 saltq_gate_after`: pending on dependency
- `3282992 salt1_nom_cont`: pending on priority
