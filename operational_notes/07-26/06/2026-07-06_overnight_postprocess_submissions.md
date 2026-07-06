# Overnight Postprocess Submissions

Date: `2026-07-06`
Task: `AGENT-180`

## Decision

Submit the three requested overnight lanes:

1. Water postprocess rerun after Water continuation `3265970` timed out and the first dependent postprocess `3275363` failed on extra `sacct` fields: submitted as `3278452` (`water_post_rerun`).
2. Corrected Salt Q postprocess/gate after live jobs `3275448`, `3275449`, and `3275560` finish: submitted as `3278453` (`saltq_gate_after`) with dependency `afterany:3275448:3275449:3275560`.
3. Jin per-leg gap analysis rerun with the Fluid model root added to `PYTHONPATH`: submitted as `3278454` (`jin_gap_rerun`).

## Intent and Admission Rules

The Salt job is an admission gate, not closure fitting. It writes a solver/preflight audit summary and a monitor-based run-status inventory. Corrected Salt rows remain inadmissible unless the operating-point gate reports `requalified`.

The Water job uses `--no-sacct` with explicit job-state overrides to avoid the `job_start/job_end/...` CSV-field failure seen in `3275363`.

The Jin gap job uses copied scripts under `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/` so the rerun writes task-scoped outputs instead of overwriting the failed July 4 directory.

## Files

- `tmp/2026-07-06_overnight_postprocess_jobs/run_water_postprocess_rerun.sbatch`
- `tmp/2026-07-06_overnight_postprocess_jobs/run_corrected_salt_postprocess_afterany.sbatch`
- `tmp/2026-07-06_overnight_postprocess_jobs/run_jin_perleg_gap_rerun.sbatch`
- `tmp/2026-07-06_overnight_postprocess_jobs/slurm-corrected_saltq_all_prepared-3275560.out`
- `tmp/2026-07-06_overnight_postprocess_jobs/collect_corrected_salt_status.py`

## Morning Pickup

Check Slurm states and logs first. Then inspect:

- `sacct -j 3278452,3278453,3278454 --format=JobID,JobName%28,State,ExitCode,Elapsed`
- `work_products/2026-07-06_overnight_postprocess_jobs/water_postprocess_after_3265970/run_status/`
- `work_products/2026-07-06_overnight_postprocess_jobs/corrected_salt_after_3275448_3275449_3275560/`
- `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/`
