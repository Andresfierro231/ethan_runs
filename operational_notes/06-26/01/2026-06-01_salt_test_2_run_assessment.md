# Salt Test 2 Run Assessment

Date: `2026-06-01`
Source ID: `val_salt_test_2_coarse_mesh_laminar`
Case ID: `salt_test_2`

## Decision

- The current case needs a longer run before it should be treated as a completed validation-quality sample.
- Any longer run should be staged in its own writable folder, not in the imported source directory.

## Evidence Used

- `system/controlDict` requests `stopAt endTime` with `endTime 10000`.
- `logs/log.foamRun` stops at `Time = 1724.714285714s` and ends with Slurm cancellation plus `KILLED BY SIGNAL: 15 (Terminated)`.
- `case_config.yaml` defines a QoI convergence target of `rtol = 1.0e-4` over a `100`-sample window.

## Convergence Check

Last-two-window comparison using the final two `100`-sample blocks from postProcessing:

- `mdot_pipeleg_left_04_test_section`: relative change `-2.6913e-4`
- `mdot_pipeleg_lower_05_straight`: relative change `-2.6841e-4`
- `mdot_pipeleg_right_02_middle`: relative change `-2.6775e-4`
- `mdot_pipeleg_upper_05_cooler`: relative change `-2.6852e-4`
- `total_Q`: relative change `+3.0845e-2`
- `probe_T_mean`: relative change `+9.3757e-5`

Last-window span relative to last-window mean:

- mdot monitors: about `5.30e-4`
- `total_Q`: about `7.60e-2`
- `piv_T`: about `1.0412e-4`
- `probe_T_mean`: about `1.6483e-4`

## Interpretation

- The case is closest to convergence in the temperature signals.
- The mdot monitors are better behaved than the heat-loss metric, but they are still above the configured `1.0e-4` tolerance.
- The derived external heat-loss quantity is clearly not converged by the stated QoI rule and is still trending upward near the end of the run.
- Because the run also stopped far short of the configured `endTime`, the safer interpretation is that the current outputs are useful diagnostics, not final validation outputs.

## Render Retry

- Submitted render retry job: `3199773`
- Scheduler result: `COMPLETED`, exit code `0:0`, elapsed `00:00:21`
- Render artifact result: still `skipped`
- Recorded reason: `paraview_5_10 failed without output.`
- Slurm output captured locally at `slurm-3199773.out`

## Required Follow-up

- Keep the imported source under `/scratch/09748/andresfierro231/projects_scratch/val_salt_test_2_coarse_mesh_laminar` read-only.
- Stage any continuation under `jadyn_runs/salt2/2026-06-01_continuation_candidate/`.
- After continuation, regenerate QoI and validation summaries and re-check convergence before updating downstream interpretation.
