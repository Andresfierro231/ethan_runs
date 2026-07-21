---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/non_upcomer_f6_candidate_matrix.csv
  - work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/right_leg_downcomer_sampling_contract.csv
tags: [pressure-ledger, f6, non-upcomer, downcomer, branch-modeling]
related:
  - .agent/journal/2026-07-20/f6-non-upcomer-branch-modeling-analysis.md
  - imports/2026-07-20_f6_non_upcomer_branch_modeling_analysis.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: status
status: complete
---
# TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS Status

## Objective

Assess whether F6 can be modeled from non-upcomer, non-corner branches, with
priority on the right-leg/downcomer-like branch and secondary attention to the
test-section straight span.

## Outcome

Complete. The analysis selects exactly six ordinary future F6 candidates:
Salt2/Salt3/Salt4 `right_leg` and Salt2/Salt3/Salt4 `test_section_span`. None
is fit-ready today because raw endpoint pairs, same-window endpoint evidence,
geometry attachment, and same-QOI mesh/time UQ are missing. Upcomer, corners,
junctions, component/cluster rows, and material-reverse-flow rows are excluded
from the ordinary single-stream F6 lane.

## Changes Made

- `work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/**`
- `.agent/BOARD.md`
- `.agent/status/2026-07-20_TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS.md`
- `.agent/journal/2026-07-20/f6-non-upcomer-branch-modeling-analysis.md`
- `imports/2026-07-20_f6_non_upcomer_branch_modeling_analysis.json`
- `operational_notes/maps/pressure-and-momentum-budget.md`

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/build_f6_non_upcomer_branch_modeling_analysis.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/test_f6_non_upcomer_branch_modeling_analysis.py`
  passed: 7 tests.
- `python3.11 tools/docs/build_repo_index.py --check`
  passed.
- `python3.11 tools/agent/source_property_gate.py ... --warn`
  passed with `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/preflight_task.py --task-id TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS`
  passed: no conflicts detected.
- `python3.11 tools/agent/finish_task.py --task-id TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS`
  passed.

## Remaining Blockers

- Right-leg/downcomer and test-section-span endpoint pairs are not harvested.
- Same-QOI mesh/time UQ is missing for the branch pressure residual.
- F6 remains blocked until a future endpoint sampler and gate review compare
  residual movement against `F3_shah_apparent`.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Scheduler state was not mutated. Fluid and external repositories were
not edited. No solver/postprocessing launch, F6 fit, component-K admission,
ordinary-K promotion, hidden global multiplier, clipped K, model selection,
blocker-register mutation, or endpoint-pressure invention was performed.
