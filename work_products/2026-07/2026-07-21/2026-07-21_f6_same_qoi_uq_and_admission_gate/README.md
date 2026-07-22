---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/endpoint_pair_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/mesh_uq_implication.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/same_qoi_uq_summary_by_family.csv
tags: [f6, same-qoi-uq, admission-gate, diagnostic, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/README.md
task: TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE
date: 2026-07-21
role: Hydraulics / Reviewer / Tester / Writer
type: work_product
status: complete
---
# F6 Same-QOI UQ And Admission Gate

This package closes the current F6 admission gate from harvested Stage A face
metrics, repaired coarse provenance, and the same-QOI UQ execution context.

Open first:

1. `f6_candidate_admission_decision.csv`
2. `gate_rollup.csv`
3. `f3_comparison_status.csv`
4. `summary.json`

Result: `12` decision rows were labeled with the allowed
label set. `12` rows are diagnostic. No F6 fit,
component K, cluster K, clipped K, or global multiplier is admitted.
