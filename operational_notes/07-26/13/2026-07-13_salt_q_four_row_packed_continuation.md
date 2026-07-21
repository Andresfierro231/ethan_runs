# Salt-Q Four-Row Packed Continuation

Date: `2026-07-13`

## Decision

Salt4 +10Q was not converged enough to postprocess as terminal evidence. Include
it in the packed continuation with `salt2_lo10q`, `salt2_hi10q`, and
`salt4_lo10q`.

## Evidence

Final available `salt4_hi10q` window: `12039` to `12639 s`.

- `total_Q`: drift `-1.59099 W`, span `1.69738 W`, latest `6.99361 W`.
- Four mdot monitors: final-window drifts around `1.13e-4 kg/s`, about `0.61%`
  of mean, with spans around `2.4%` of mean.
- Fluid temperature probes: max drift `1.45105 K`, max span `4.73688 K`.
- Wall temperature probes: max drift `1.52954 K`, max span `4.07394 K`.

## Launch Plan

Use
`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/run_selected_corrected_salt_q_continuation.sbatch`.

Packed rows:

- `salt2_lo10q`
- `salt2_hi10q`
- `salt4_lo10q`
- `salt4_hi10q`

The job is one node, `256` Slurm tasks, four cases, and `64` ranks per case.
The launcher now refuses more than four cases or more case ranks than allocated
tasks.

Before submission, selected staged `system/functions` files for `salt2_lo10q`,
`salt2_hi10q`, and `salt4_lo10q` were changed to diagnostic-only convergence
monitor behavior, matching `salt4_hi10q`. They no longer call
`stopAt(writeNow)`.

## Submission

Submitted from `login3` as Slurm job `3293441`.

Initial checks:

- `squeue`: `RUNNING`, node `c318-011`, time limit `5-00:00:00`.
- Slurm step view: four active `foamRun` steps, `3293441.0` through
  `3293441.3`.
- Slurm stdout: all four restart fields patched at `10291`, `9674`, `11655`,
  and `12639`, then all four cases launched.

## Follow-Up

After launch, confirm the Slurm job ID and queue state, then check each
case-local `logs/log.foamRun_corrected_q` for runtime advancement beyond its
restart time. Re-run the corrected-Q convergence gate only after late windows
exist.
