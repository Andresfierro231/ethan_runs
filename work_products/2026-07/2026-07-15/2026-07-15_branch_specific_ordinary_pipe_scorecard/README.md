---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan/current_evidence_recirculation_classification.csv
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_fit_candidate_table.csv
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/internal_nu_h_proxy_review.csv
  - operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md
  - operational_notes/07-26/15/2026-07-15_branch_specific_model_forms_and_upcomer_omission_plan.md
tags: [branch-scorecard, ordinary-pipe, upcomer-excluded, forward-v1]
task: AGENT-442
date: 2026-07-15
type: work_product_readme
status: complete
---
# Branch-Specific Ordinary-Pipe Scorecard

This package implements the AGENT-442 branch mask for ordinary-pipe analysis.
It does not fit `Nu`, `f_D`, or `K` from current upcomer rows.

## Result

- Evidence rows reviewed: `28`.
- Current ordinary-pipe fit rows admitted: `0`.
- Upcomer evidence rows reviewed: `25`.
- Upcomer ordinary-pipe fit rows admitted: `0`.

Current result: no ordinary-pipe coefficient fit is admitted from the available
rows. The current upcomer evidence remains a recirculation/onset or
section-effective diagnostic lane.

## Outputs

- `ordinary_pipe_candidate_rows.csv`: row-level evidence classification.
- `branch_specific_fit_mask.csv`: branch masks and included/excluded labels.
- `branch_model_equations.csv`: equations and gate requirements.
- `summary.json`: machine-readable closeout.

## Guardrails

Native CFD outputs, registry/admission state, generated indexes, and external
`../cfd-modeling-tools/**` were not mutated.
