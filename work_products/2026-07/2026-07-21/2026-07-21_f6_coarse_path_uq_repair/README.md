---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/blocked_coarse_endpoint_face_matrix.csv
  - work_products/2026-07/2026-07-20/2026-07-20_f6_coarse_path_repair_endpoint_harvest/repaired_case_source_inventory.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/summary.json
tags: [f6, coarse-repair, mesh-uq, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-COARSE-PATH-UQ-REPAIR.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/README.md
task: TODO-F6-COARSE-PATH-UQ-REPAIR
date: 2026-07-21
role: cfd-pp / Mesh-GCI / Tester / Writer
type: work_product
status: complete
---
# F6 Coarse Path UQ Repair

The 12 coarse endpoint rows are source-path repaired to retained reconstructed
cases with `p_rgh`, `U`, `rho`, and `T`; they can support a future Stage B
VTK/area/recirculation sampler. They do not yet provide full same-QOI static
pressure evidence because static `p` is absent in the repaired coarse
reconstructions.

Open first:

1. `coarse_source_repair_audit.csv`
2. `coarse_vtk_sampling_decision.csv`
3. `mesh_uq_implication.csv`
4. `summary.json`

No scheduler job, F6 fit, component-K admission, clipped K, or hidden multiplier
is introduced here.
