# Selected corrected Salt Q steadiness and packed resubmit

Date: `2026-07-10`

## Scope

Selected corrected-Q perturbation rows only:

- `salt1_jin_lo10q_corrected`
- `salt1_jin_hi10q_corrected`
- `salt4_jin_hi10q_corrected`

These rows remain labeled `sensitivity/correlation-support`; none is promoted into nominal baseline or closure-fit evidence by this package.

## Observations

- `salt1_jin_lo10q_corrected`: mdot is steady over the latest 300 s window, but total_Q is still drifting and the formal 3280969 gate verdict is `too_short`. Continue, but do not admit.
- `salt1_jin_hi10q_corrected`: the prior run stopped after only about 254 s of post-restart advance. Its mdot window is only quasi-steady and total_Q is drifting. The Salt1 diagnostic monitor repair is present, so continuation is appropriate now that the early stop path is disabled.
- `salt4_jin_hi10q_corrected`: mdot is steady over the latest 300 s window, but total_Q is still drifting and the formal 3280969 gate verdict is `too_short`. Its staged convergence monitor still had `writeNow` stop authority, so this package changed that selected staged monitor to diagnostic-only before resubmission.

## Staged input changes

The selected staged OpenFOAM inputs were changed only to prevent immediate or weak-monitor stops:

- Salt1 -10Q `controlDict`: `endTime 9756.33125` -> `30000`.
- Salt1 +10Q `controlDict`: `endTime 9756.33125` -> `30000`.
- Salt4 +10Q `controlDict`: `endTime 16000` -> `30000`.
- All three selected `controlDict`s: `timePrecision 9` -> `12`.
- Salt4 +10Q `system/functions`: convergence monitor now logs diagnostic convergence and continues to configured `endTime`, matching the Salt1 corrected-Q diagnostic-only behavior.
- Salt1 +10Q selected launcher override: restart from patched integer time `4010`; the fractional final write `4010.590361446` repeatedly failed OpenFOAM `T` lookup at thermo initialization.

## Sources

- Gate verdicts: `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_gate_3280969_review/row_verdicts.csv`
- Prior minimal plan: `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_minimal_continuation_plan/convergence_resubmit_recommendations.csv`
- Time-series steadiness: `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv`
- Launcher: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/run_selected_corrected_salt_q_continuation.sbatch`

## Decision

Submit exactly these three rows as one one-node packed Slurm continuation. Do not bulk-resubmit the corrected-Q campaign.

Final active job: `3288671` (`saltq_sel_cont`) on one NuclearEnergy node. Startup snapshot showed all three `foamRun` steps running and advancing:

- Salt1 -10Q: latest observed log time `6377.3896103896232 s`.
- Salt1 +10Q: latest observed log time `4010.234939759036 s`.
- Salt4 +10Q: latest observed log time `11536.26760563383 s`.
