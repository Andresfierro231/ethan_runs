---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/coarse_vtk_sampling_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/stage_a_endpoint_face_matrix.csv
tags: [f6, coarse-vtk, raw-face, recirculation, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-COARSE-VTK-SAMPLER-SUBMIT.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/README.md
task: TODO-F6-COARSE-VTK-SAMPLER-SUBMIT
date: 2026-07-21
role: Scheduler / cfd-pp / Tester / Writer
type: work_product
status: complete
---
# F6 Stage B Coarse VTK Sampler

This package prepares and submits the coarse F6 raw-face sampler for the twelve
repaired endpoint rows. It samples `p_rgh`, `U`, `rho`, and `T` only. Static
`p` is absent and remains an explicit same-QOI pressure-basis blocker.

Open first:

1. `stage_b_coarse_endpoint_face_matrix.csv`
2. `coarse_raw_face_metrics.csv`
3. `coarse_pair_diagnostics.csv`
4. `coarse_static_pressure_blocker.csv`
5. `RUNNING.md`

Summary: `12` endpoint rows are in scope;
`12` are currently sampled in harvested output.
No F6 fit, component K, cluster K, clipped K, or global multiplier is admitted.
