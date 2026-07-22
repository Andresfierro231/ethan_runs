---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_face_area_vector_repair_rerun/rerun_readiness_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_face_vector_exact_label_slurm_rerun/run_face_vector_exact_label_sampler.sbatch
tags: [s13, upcomer-exchange, slurm, exact-label, journal, superseded]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-FACE-VECTOR-EXACT-LABEL-SLURM-RERUN-2026-07-22.md
  - imports/2026-07-22_s13_upcomer_exchange_face_vector_exact_label_slurm_rerun.json
task: TODO-S13-UPCOMER-EXCHANGE-FACE-VECTOR-EXACT-LABEL-SLURM-RERUN-2026-07-22
date: 2026-07-22
role: Scheduler/Implementer/Tester/Writer
type: journal
status: complete
---
# S13 face-vector exact-label Slurm rerun

## Attempted

Claimed the fresh scheduler rerun after the face-vector repair gate showed the
current source is ready and the old exact-label sampler package remains
fail-closed.

Submitted task-owned Slurm wrapper through `login3`; Slurm returned job
`3311004`.

After the user clarified that a one-case/window smoke must run before any full
six-case rerun, canceled `3311004` and moved the active gate to the clean smoke
package under `TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22`.

## Observed

The rerun must write to a new package with `--out`; the old fail-closed package
must remain immutable evidence.

Initial queue/accounting checks showed `3311004` pending for resources. A later
check showed it running on `c318-012`. Final accounting after cancellation
showed `3311004` and its batch step `CANCELLED`, exit code `0:15`, ending
`2026-07-22T11:42:10`.

The package emitted partial Salt2 medium/fine face files before cancellation.
The Salt2 medium exchange-interface CSV header includes `area_vector_x_m2`,
`area_vector_y_m2`, and `area_vector_z_m2`, confirming the writer-side contract
is repaired. Because the job was canceled mid-run, those partial files are
superseded/non-admissible.

## Inferred

This row should not be consumed for harvest, mesh/GCI, or admission. It now
documents a superseded scheduler attempt and the partial face-header
observation only.

## Next Useful Actions

1. Monitor clean smoke job `3311109` in the face-area repair package.
2. Inspect the smoke `summary.json`, `sampling_error_log.csv`,
   `medium_fine_exact_label_qoi_rows.csv`, and
   `faces/salt_2_medium_exchange_interface_faces.csv`.
3. Only after smoke success, claim/submit a full six-case rerun row.
