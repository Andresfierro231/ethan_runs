---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/endpoint_pair_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/coarse_pair_diagnostics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/summary.json
tags: [f6, stage-b-qa, gate-refresh, recirculation, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-STAGE-B-HARVEST-QA-AND-GATE-REFRESH.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/README.md
task: TODO-F6-STAGE-B-HARVEST-QA-AND-GATE-REFRESH
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: work_product
status: complete
---
# F6 Stage B Harvest QA And Gate Refresh

This package merges Stage A medium/fine and Stage B coarse F6 endpoint evidence
into one diagnostic QA and gate-refresh result.

Open first:

1. `stage_a_b_face_qa.csv`
2. `stage_a_b_pair_qa.csv`
3. `f6_gate_refresh.csv`
4. `blocker_delta.csv`
5. `summary.json`

Result: `20` endpoint faces and `10`
endpoint pairs are represented. All `10` pair
rows remain diagnostic. Coarse static `p` remains blocked, and no F6/component-K
admission is made.
