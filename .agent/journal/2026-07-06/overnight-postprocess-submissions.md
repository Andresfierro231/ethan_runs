# Overnight Postprocess Submissions

Date: `2026-07-06`
Task: `AGENT-180`
Role: Coordinator / Implementer / Writer

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

## Submission Design

- Water rerun: same monitor/status workflow, but with `--no-sacct` and explicit job-state overrides.
- Corrected Salt: `afterany:3275448:3275449:3275560`, then collect solver/preflight summaries and run the operating-point gate from a static prepared-case manifest.
- Jin gap: copied the two analysis scripts into the July 6 work-product root and set `PYTHONPATH` to `../cfd-modeling-tools/tamu_first_order_model/Fluid`.

## Submitted Jobs

- `3278452` `water_post_rerun`, development partition, `00:45:00`, pending on resources at submission check.
- `3278453` `saltq_gate_after`, development partition, `01:30:00`, dependency `afterany:3275448:3275449:3275560`, pending on dependency at submission check.
- `3278454` `jin_gap_rerun`, development partition, `02:00:00`, pending on resources at submission check.

Submission command was run through `ssh login3` from compute host `c318-008`.

## Admission Boundary

Corrected Salt outputs are not automatically closure-fit data. The postprocess job is an admission gate. Only `requalified` operating-point rows may feed later closure fitting or 1D model comparison.
