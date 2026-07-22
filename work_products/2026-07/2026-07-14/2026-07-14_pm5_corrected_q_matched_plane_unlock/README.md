---
provenance:
  task: AGENT-357
  generated_by: codex
tags: [cfd-pp, upcomer, matched-plane, corrected-q, perturbed-q, salt]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction/README.md
---
# PM5 Corrected-Q Matched-Plane Unlock

## Why This Exists

The Salt2/Salt4 +/-5Q perturbed-Q harvest completed under Slurm job `3295437`.
The older matched-plane readiness table still said `wait_for_corrected_q_harvest_job_3295437`, so this package converts that stale dependency into a runnable compute job.

## What Was Unlocked

Four harvested rows now have an explicit matched-plane compute case list:

- `salt2_lo5q` / `salt2_jin_lo5q_corrected`, time `10275`, holdout
- `salt2_hi5q` / `salt2_jin_hi5q_corrected`, time `9780`, holdout
- `salt4_lo5q` / `salt4_jin_lo5q_corrected`, time `11695`, training
- `salt4_hi5q` / `salt4_jin_hi5q_corrected`, time `11399`, training

The important fix is geometry labeling: these corrected/perturbed run keys use
the parent Jin mesh station files:

- Salt2: `viscosity_screening_salt_test_2_jin_coarse_mesh`
- Salt4: `viscosity_screening_salt_test_4_jin_coarse_mesh`

## Submitted Job

Submitted:

```bash
ssh login3.ls6.tacc.utexas.edu "/usr/bin/sbatch /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/scripts/submit_pm5_matched_plane_compute.sbatch"
```

Original Slurm job:

- Job id: `3295901`
- Name: `upc_pm5q`
- Partition: `normal`
- Final state: `CANCELLED`
- Initial reason: `Priority`

The original normal-queue job was canceled on `2026-07-14` and the sbatch
script was changed to submit to `NuclearEnergy`.

Second Slurm job:

- Job id: `3295968`
- Name: `upc_pm5q`
- Partition: `NuclearEnergy`
- Final state: `CANCELLED`
- Initial reason: `Priority`

The NuclearEnergy batch job was canceled on `2026-07-14` because the workload
was moved onto the active interactive compute allocation.

Completed interactive run:

- Run id: `interactive_3295120_retry2`
- Allocation job id: `3295120`
- Allocation partition: `NuclearEnergy-dev`
- Host: `c318-008.ls6.tacc.utexas.edu`
- Launch method: `srun -N1 -n1`
- Final state: `COMPLETED`
- Exit code: `0`
- Finished at: `2026-07-14T18:01:29-05:00`
- Status file: `interactive_srun_status.txt`
- Restart note: `interactive_3295120` and `interactive_3295120_retry1` failed
  on the first `salt2_lo5q` surfaces pass because the staging copy inherited a
  source-case `system/functions` file. The runner now disables that file or
  directory in tmp staging before postprocessing.

Monitor:

```bash
sed -n '1,80p' work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/interactive_srun_status.txt
tail -80 work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/logs/upcomer_pm5q-interactive_3295120_retry2.out
tail -80 work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/logs/upcomer_pm5q-interactive_3295120_retry2.err
```

Expected parsed outputs after completion:

- `parsed/matched_plane_metrics_salt2_lo5q.csv`
- `parsed/matched_plane_metrics_salt2_hi5q.csv`
- `parsed/matched_plane_metrics_salt4_lo5q.csv`
- `parsed/matched_plane_metrics_salt4_hi5q.csv`

Completion outcome:

- All four CSVs were written with three rows each.
- All twelve rows are currently `metric_status=incomplete` and
  `quality_flags=blocked-missing-field`.
- Parser failure mode: sampled plane files are missing one of required fields
  `U/rho/T`; sampled wall files are missing wall `T` or `wallHeatFlux`.
- These outputs are provenance and blocker evidence, not admitted matched-plane
  metrics.

## Salt1 Caveats

Salt1 nominal and lo10q are admitted for training under these caveats:

- Terminal/steady/postprocessing evidence exists, but BC role promotion is still partial case-level evidence rather than a patch-complete terminal BC table.
- The admission is a dated policy override for training/correlation support. The perturbation rows must remain labeled as perturbations and must not be silently collapsed into the nominal baseline.
- Thermal closure admission does not imply matched pressure/upcomer metric admission.

For `salt1_hi10q`, the conflict is not a new CFD failure. It is an evidence-ordering conflict: the older Salt inventory used a stale/latest-time gate and marked the row failed/not-admissible, while the later Salt1 terminal harvest package records terminal stationary evidence at `4987-5587 s`. Remove the caveat by writing a superseding curator note or refreshed Salt1 inventory row that trusts the terminal harvest package over the older latest-time table.

## Remaining Issues

- Current job `3295968` must finish and parsed metrics must be reviewed before pressure/upcomer rows can be admitted.
- If OpenFOAM reconstruction or `foamPostProcess` fails for a row, inspect that row's `logs/reconstruct_*`, `logs/wallHeatFlux_*`, and `logs/surfaces_*` files.
- The original AGENT-344 readiness CSV remains stale for +/-5Q until a later refresh consumes this package.

## Guardrails

Native CFD source trees under `jadyn_runs/**` are read-only. The job writes only to this work-product package and `tmp/2026-07-14_pm5_corrected_q_matched_plane_unlock/`.
