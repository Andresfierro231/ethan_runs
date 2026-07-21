# 2026-07-13 Salt2 Fine Reconstructed-T Repair Plan Sbatch

Task: `AGENT-291`

This note records continuity for the next project step: fine Salt2 refined
thermal extraction is the immediate blocker for thermal UA/HTC/Nu mesh-family
work. The run is a repair gate, not a closure admission.

The workflow is documented in:

- `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/README.md`

Estimated runtime is `3-6 hours`; the batch request uses `12:00:00` walltime.
The job should produce a separate fine repair-trial output package instead of
overwriting AGENT-267 medium evidence.

Submission:

- Direct `sbatch` on the current compute node was refused.
- Submitted through `login3`.
- Slurm job: `3293768`
- Initial state: `PENDING` for `(Resources)`.
- Latest pre-handoff state: `RUNNING` on `c318-016`.

Admission boundary: no thermal UA/HTC/Nu value should be used for closure
interpretation until terminal Slurm evidence and fine `summary.json` gates are
reviewed.

Terminal closeout:

- Job `3293768` (`s2_fine_T+`) completed with exit `0:0`.
- Elapsed time was `00:22:33` on `c318-016`.
- Fine smoke passed clean reconstructed `T`, section sampling, and segment
  thermal extraction.
- The missing-fine-thermal-extraction blocker is closed, but thermal closure
  interpretation remains blocked by the follow-up thermal mesh gate:
  `work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/`.
