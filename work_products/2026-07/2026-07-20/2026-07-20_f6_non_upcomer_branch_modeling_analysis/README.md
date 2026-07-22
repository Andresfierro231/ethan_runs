---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/legwise_anchor_inventory.csv
  - work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/f3_vs_legwise_f6_admission_gate.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/pressure_f6_next_gate.csv
tags: [pressure-ledger, f6, non-upcomer, downcomer, branch-modeling]
related:
  - .agent/status/2026-07-20_TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS.md
  - .agent/journal/2026-07-20/f6-non-upcomer-branch-modeling-analysis.md
task: TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: work_product
status: complete
---
# F6 Non-Upcomer Branch Modeling Analysis

Generated: `2026-07-20T23:53:19+00:00`

## Decision

The preferred ordinary F6 analysis lane is non-upcomer and non-corner:
Salt2/Salt3/Salt4 `right_leg` and `test_section_span`. These six rows are
credible future branch candidates, but none is fit-ready today because raw
endpoint pairs and same-QOI mesh/time UQ are missing.

## Outputs

- `non_upcomer_f6_candidate_matrix.csv`
- `right_leg_downcomer_sampling_contract.csv`
- `test_section_span_sampling_contract.csv`
- `f6_branch_model_form_contract.csv`
- `same_qoi_uq_requirements.csv`
- `f3_vs_branch_f6_gate.csv`
- `paper_methods_non_upcomer_f6_note.md`
- `source_manifest.csv`
- `summary.json`

## Counts

- Inventory rows reviewed: `36`.
- Ordinary non-upcomer candidates: `6`.
- Fit-ready rows today: `0`.
- F6 fits performed: `0`.

## Guardrails

No scheduler work, native CFD/OpenFOAM mutation, registry/admission mutation,
Fluid edit, solver/postprocessing launch, F6 fit, component-K admission, hidden
global multiplier, clipped K, or endpoint-pressure invention was performed.
