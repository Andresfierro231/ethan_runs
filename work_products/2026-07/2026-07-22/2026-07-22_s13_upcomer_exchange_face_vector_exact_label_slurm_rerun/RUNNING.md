---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_face_vector_exact_label_slurm_rerun/run_face_vector_exact_label_sampler.sbatch
tags: [s13, upcomer-exchange, slurm, superseded]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-FACE-VECTOR-EXACT-LABEL-SLURM-RERUN-2026-07-22.md
task: TODO-S13-UPCOMER-EXCHANGE-FACE-VECTOR-EXACT-LABEL-SLURM-RERUN-2026-07-22
date: 2026-07-22
role: Scheduler/Monitor handoff
type: handoff
status: complete
---
# S13 Face-Vector Exact-Label Slurm Rerun

Submitted Slurm job: `3311004`.

Initial state: `PENDING` for `Resources`; no node assigned.

Latest observed state: `CANCELLED`. It started on `c318-012` at
`2026-07-22T11:14:17` and ended at `2026-07-22T11:42:10` with exit code
`0:15`.

This package is superseded by the smoke-first gate. It produced partial Salt2
medium/fine face files before cancellation. Those partial files are not
admissible production, mesh/GCI, or harvest evidence.

Observed header check:

`faces/salt_2_medium_exchange_interface_faces.csv` contains
`area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2`, so this
superseded package supports the narrow writer-contract observation only.

Active next step: monitor clean smoke job `3311109` in
`work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/smoke_salt2_medium_one_window/`.

Do not run mesh/GCI, production harvest, Qwall/source-property release,
coefficient admission, final score, or S11/S12/S13/S15/S6 trigger from this
row.
