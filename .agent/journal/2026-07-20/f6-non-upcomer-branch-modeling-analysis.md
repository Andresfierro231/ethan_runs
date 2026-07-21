---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/paper_methods_non_upcomer_f6_note.md
tags: [journal, pressure-ledger, f6, non-upcomer, downcomer]
related:
  - .agent/status/2026-07-20_TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS.md
  - imports/2026-07-20_f6_non_upcomer_branch_modeling_analysis.json
task: TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: journal
status: complete
---
# F6 Non-Upcomer Branch Modeling Analysis

Task: `TODO-F6-NON-UPCOMER-BRANCH-MODELING-ANALYSIS`

## Work Completed

Built an analysis package from the legwise F6 pressure-anchor inventory and
pressure/F6 blocker-unlock gates. The package classifies all 36 rows, selects
six ordinary future candidates, emits right-leg/downcomer and test-section-span
sampling contracts, defines the F3-relative branch residual model form, and
records same-QOI UQ requirements.

## Scientific Decision

The ordinary F6 lane should focus first on `right_leg`, which is the current
downcomer-like straight branch, then `test_section_span`. Current rows are not
fit-ready. Upcomer, corner, junction, component/cluster, and material
reverse-flow rows remain excluded from ordinary single-stream F6.

## Next Evidence Needed

- downstream/upstream endpoint labels for `right_leg` and `test_section_span`;
- same-window endpoint `p`, `p_rgh`, `U`, `rho`, `T`, area, normal, RAF/RMF/SVF,
  Re/Ri, and source/property labels;
- same-label/same-formula/same-sign mesh/time UQ;
- later F6 gate review against `F3_shah_apparent`.

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/build_f6_non_upcomer_branch_modeling_analysis.py`
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/test_f6_non_upcomer_branch_modeling_analysis.py`

Both passed before closeout.
