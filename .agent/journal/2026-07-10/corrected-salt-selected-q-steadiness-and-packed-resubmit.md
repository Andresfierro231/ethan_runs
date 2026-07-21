# Corrected Salt selected-Q steadiness and packed resubmit

Task: AGENT-249

## Observed evidence

- The completed 3280969 gate marked `salt1_jin_lo10q_corrected`, `salt1_jin_hi10q_corrected`, and `salt4_jin_hi10q_corrected` as `too_short` and not closure-fit admissible.
- Time-series checks show `salt1_jin_lo10q_corrected` and `salt4_jin_hi10q_corrected` have steady mdot over their latest 300 s windows, while `total_Q` still has a resolved drift.
- `salt1_jin_hi10q_corrected` had only about 254 s of post-restart advance and a prior early-stop history, so it needs continuation after monitor repair.
- Pre-submit inspection found Salt1 corrected-Q monitors already diagnostic-only. Salt4 +10Q still had `Time::stopAtControl::writeNow` in the staged `system/functions`.

## Actions

- Extended selected staged `controlDict` `endTime` values to `30000`.
- Set selected staged `timePrecision` values to `12`.
- Changed the selected Salt4 +10Q convergence monitor to diagnostic-only logging, matching the Salt1 corrected-Q behavior.
- Added a selected-only packed Slurm launcher: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/run_selected_corrected_salt_q_continuation.sbatch`.
- Added optional `--processor-time` to the corrected-Q patcher so the selected launcher can patch Salt1 +10Q restart `4010`.
- Wrote the row-level summary in `work_products/2026-07/2026-07-10/2026-07-10_corrected_salt_selected_q_steadiness_packed_resubmit/`.
- Submitted final active job `3288671`; startup accounting showed all three `foamRun` steps running.

## Interpretation

These rows look promising in mdot, especially Salt1 -10Q and Salt4 +10Q, but they are not steady/admissible enough for closure fits. Continue only these selected rows and re-gate afterward. Keep them labeled as sensitivity/correlation-support.

## Validation

- `bash -n jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/run_selected_corrected_salt_q_continuation.sbatch`
- `python3.11 -m py_compile jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/patch_q_fields.py`
- `rg -n "endTime|stopAtControl::writeNow|stopAt\\s*\\(\\s*writeNow|diagnostic criterion met|continuing to configured endTime" ...selected staged controlDict/functions...`
- `sacct -j 3288671 --format=JobID,JobName,State,Elapsed,ExitCode,NodeList,Reason%40`

## End-of-day update

Later scheduler accounting showed the packed continuation was only partially
healthy:

- `3288671.0`: `RUNNING`
- `3288671.1`: `RUNNING`
- `3288671.2`: `FAILED` after `00:02:33`

The end-of-day wrap-up mapped `3288671.2` to
`salt4_jin_hi10q_corrected`. The failure is an OpenFOAM maximum time-precision
failure at current time name `11536.488262910847`. This should be handled as a
targeted start-time / restart-name / `timePrecision` repair, not as evidence
that the corrected-Q physics failed and not as a reason to bulk-resubmit the
corrected-Q set.

Salt1 corrected-Q steps remain live under the packed job. All selected
corrected-Q rows remain sensitivity/correlation-support and are not closure-fit
admissible until terminal post-continuation gates explicitly admit them.
