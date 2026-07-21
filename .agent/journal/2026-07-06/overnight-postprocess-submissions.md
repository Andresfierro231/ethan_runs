# Overnight Postprocess Submissions

Date: `2026-07-06`
Task: `AGENT-180`
Role: Coordinator / Implementer / Writer
Worktree: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

## Context

The user asked to submit the viable overnight postprocess lanes:

1. Water postprocess rerun.
2. Corrected Salt Q postprocess/gate after the running Salt jobs finish.
3. Jin per-leg gap analysis rerun on `sbatch`.

## Observed Starting State

- Corrected Salt jobs `3275448`, `3275449`, and `3275560` were running cleanly with no FOAM fatal errors in logs and clean preflight audit CSVs.
- Water continuation `3265970` had timed out.
- Dependent Water postprocess `3275363` failed because `build_postprocessing_run_status_inventory.py` received `sacct` fields not listed in its CSV fieldnames.
- Jin per-leg gap job `3275531` failed immediately with `ModuleNotFoundError: No module named 'tamu_loop_model_v2'`.

## Files Inspected

- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/status/2026-07-04_AGENT-177.md`
- `.agent/status/2026-07-04_AGENT-178.md`
- `.agent/journal/2026-07-04/water-postprocess-and-closure-table.md`
- `.agent/journal/2026-07-04/salt-perturbation-quarantine-and-corrected-relaunch.md`
- `tmp/2026-07-04_water_postprocess_job/slurm-water_post_3265970-3275363.err`
- `work_products/2026-07-04_jin_perleg_gap_analysis/slurm-jin_perleg_gap-3275531.err`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/README.md`
- `.agent/README.md`
- `.agent/status/README.md`
- `.agent/journal/README.md`
- `.agent/JOURNAL_POLICY.md`

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-06_AGENT-180.md`
- `.agent/journal/2026-07-06/overnight-postprocess-submissions.md`
- `operational_notes/07-26/06/2026-07-06_overnight_postprocess_submissions.md`
- `tmp/2026-07-06_overnight_postprocess_jobs/**`
- `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/**`

## Submission Design

- Water rerun: same monitor/status workflow, but with `--no-sacct` and explicit job-state overrides.
- Corrected Salt: `afterany:3275448:3275449:3275560`, then collect solver/preflight summaries and run the operating-point gate from a static prepared-case manifest.
- Jin gap: copied the two analysis scripts into the July 6 work-product root and set `PYTHONPATH` to `../cfd-modeling-tools/tamu_first_order_model/Fluid`.

## Submitted Jobs

- `3278452` `water_post_rerun`, development partition, `00:45:00`, pending on resources at submission check.
- `3278453` `saltq_gate_after`, development partition, `01:30:00`, dependency `afterany:3275448:3275449:3275560`, pending on dependency at submission check.
- `3278454` `jin_gap_rerun`, development partition, `02:00:00`, pending on resources at submission check.

Submission command was run through `ssh login3` from compute host `c318-008`.

## Commands Run

- `squeue -u andresfierro231`
- `sacct -u andresfierro231 -S 2026-07-04`
- `bash -n tmp/2026-07-06_overnight_postprocess_jobs/run_water_postprocess_rerun.sbatch`
- `bash -n tmp/2026-07-06_overnight_postprocess_jobs/run_corrected_salt_postprocess_afterany.sbatch`
- `bash -n tmp/2026-07-06_overnight_postprocess_jobs/run_jin_perleg_gap_rerun.sbatch`
- `python3.11 -m py_compile tmp/2026-07-06_overnight_postprocess_jobs/collect_corrected_salt_status.py work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_perleg_gap_analysis.py work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_wall_conductance.py`
- `python tools/analyze/build_postprocessing_run_status_inventory.py --no-sacct --job-log tmp/2026-07-06_overnight_postprocess_jobs/slurm-corrected_saltq_all_prepared-3275560.out --job-state 3275560=DRYRUN --output-dir /tmp/agent180_salt_manifest_smoke`
- `python tools/analyze/build_postprocessing_run_status_inventory.py --no-sacct ... --output-dir /tmp/agent180_water_smoke`
- `ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch ..."`
- `squeue -j 3278452,3278453,3278454,3275448,3275449,3275560 -o %i,%j,%T,%M,%l,%D,%R`

## Admission Boundary

Corrected Salt outputs are not automatically closure-fit data. The postprocess job is an admission gate. Only `requalified` operating-point rows may feed later closure fitting or 1D model comparison.

## Incomplete Lines

- The Water rerun intentionally avoids the `sacct` CSV-field failure, but `build_consolidated_closure_table.py` still uses its default July 4 run-status path internally. Treat the July 6 Water `run_status/` output as the authoritative Water status until the consolidation builder accepts a run-status input path.
- The Salt gate dry-run, while jobs are still in progress, reports document-only/false-steady. The dependency job must be read after live solver jobs exit.
- A copied script was briefly placed at `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap_run_jin_perleg_gap_analysis.py`; the submitted job uses the correct `jin_perleg_gap/` subdirectory copy.

## Next Steps

- Check `sacct -j 3278452,3278453,3278454 --format=JobID,JobName%28,State,ExitCode,Elapsed`.
- Inspect matching Slurm stdout/stderr logs under `tmp/2026-07-06_overnight_postprocess_jobs/`.
- Use Salt `run_status/run_status_inventory.csv` admission fields before any closure/model use.
