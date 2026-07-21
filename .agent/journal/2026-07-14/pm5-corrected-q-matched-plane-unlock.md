---
provenance:
  task: AGENT-357
  generated_by: codex
tags: [journal, cfd-pp, upcomer, matched-plane, perturbed-q]
related:
  - .agent/status/2026-07-14_AGENT-357.md
  - work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/README.md
---
# PM5 Corrected-Q Matched-Plane Unlock

## Work Performed

Resolved the stale `wait_for_corrected_q_harvest_job_3295437` blocker for the
Salt2/Salt4 +/-5Q perturbed-Q rows by creating a dedicated matched-plane compute
package with explicit parent-geometry mapping.

The generic AGENT-344 tool expects `source_id` to be a mesh-centerline key. The
perturbed rows have corrected-Q run keys, so this package maps:

- Salt2 +/-5Q -> `viscosity_screening_salt_test_2_jin_coarse_mesh`
- Salt4 +/-5Q -> `viscosity_screening_salt_test_4_jin_coarse_mesh`

## Submitted Job

Submitted through login node because the current shell is on `c318-008`:

```bash
ssh login3.ls6.tacc.utexas.edu "/usr/bin/sbatch /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/scripts/submit_pm5_matched_plane_compute.sbatch"
```

Result: `Submitted batch job 3295901`.

Initial state is pending priority.

## Salt1 Clarification

Salt1 caveats are policy/evidence hygiene caveats, not evidence that Salt1
nominal or lo10q must be rerun. The remaining gap is patch-complete terminal BC
promotion and clear split labeling.

Salt1 hi10q has an evidence-ordering conflict: old inventory says failed from
the latest-time gate; later terminal harvest says stationary. Remove by
superseding the older inventory row with the terminal harvest evidence after a
curator signoff.

## Next Gate

After job `3295901` reaches terminal state, harvest:

- Slurm stdout/stderr
- `logs/reconstruct_*`
- `logs/wallHeatFlux_*`
- `logs/surfaces_*`
- `parsed/matched_plane_metrics_*.csv`

Then classify the parsed pressure/upcomer rows by missing fields, recirculation,
secondary flow, mixed convection, and fit-admissible status.
