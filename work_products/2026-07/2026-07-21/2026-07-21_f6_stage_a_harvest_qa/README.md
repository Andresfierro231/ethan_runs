---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/raw_f6_endpoint_face_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/summary.json
tags: [f6, endpoint-sampler, harvest-qa, raw-face, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-STAGE-A-HARVEST-QA.md
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-F6-STAGE-A-HARVEST-QA
date: 2026-07-21
role: cfd-pp / Hydraulics / Tester / Writer
type: work_product
status: complete
---
# F6 Stage A Harvest QA

The Stage A sampler produced 8 sampled endpoint-face rows with finite required
fields and 8 present VTK surfaces. Scientific use remains diagnostic only:
all 4 endpoint pairs fail the ordinary-flow gate because RAF/RMF are material.

Open first:

1. `endpoint_face_qa.csv`
2. `endpoint_pair_qa.csv`
3. `qa_gate_status.csv`
4. `medium_fine_consistency.csv`

No F6 fit, component-K admission, clipped K, or hidden global multiplier is
introduced by this package.
