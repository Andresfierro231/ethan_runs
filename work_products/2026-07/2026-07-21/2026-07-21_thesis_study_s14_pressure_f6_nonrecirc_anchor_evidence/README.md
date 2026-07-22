---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/non_upcomer_f6_candidate_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/stage_a_b_pair_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s10_pressure_f6_low_recirc_anchor_uq/summary.json
tags: [thesis-dossier, s14, pressure, f6, branch-use, no-admission]
related:
  - .agent/status/2026-07-21_TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s10_pressure_f6_low_recirc_anchor_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/README.md
task: TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S14 Pressure/F6 Nonrecirculating Anchor Evidence

## Decision

S14 closes as `pressure_F6_use_map_complete_no_admitted_score`. The study scores `53`
F6-relevant rows and releases `0` admitted F6/component-K candidates.

Use-label counts:

- `admit`: `0`
- `diagnostic_only`: `11`
- `future_candidate`: `8`
- `do_not_use`: `34`

## How To Use This

Open first:

1. `f6_branch_use_scorecard.csv`
2. `f6_branch_decision_table.csv`
3. `f3_vs_f6_comparison_readiness.csv`
4. `f6_publication_claim_ledger.csv`
5. `s11_decision.csv`

Current F6 evidence may be used for diagnostic branch screening and publication
guardrails. It must not be used as a fitted F6 coefficient, component `K`,
cluster `K`, clipped `K`, or hidden global multiplier.

## Scientific Result

The preferred future ordinary F6 lanes remain `right_leg` and
`test_section_span`, but they are future candidates only. Current sampled F6
endpoint pairs remain diagnostic because ordinary-flow and same-QOI UQ gates do
not pass. Pressure-corner rows remain section-effective or pressure-recovery
diagnostics and must not be converted into F6 loss.

## Next Action

Refresh terminal low-recirculation source readiness or run a separately claimed sampler/UQ row before any F3-vs-F6 scoring release.

## Guardrails

No native OpenFOAM output, registry/admission state, scheduler state, sampler,
solver, Fluid/external repo, blocker register, generated index, fitting/model
selection, S11 trigger, clipped `K`, global multiplier, F6 fit, component `K`,
or cluster `K` was changed or produced.
