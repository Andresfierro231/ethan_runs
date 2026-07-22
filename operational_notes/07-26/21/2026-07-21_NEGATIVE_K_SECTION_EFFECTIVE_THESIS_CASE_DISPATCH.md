---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_negative_k_section_effective_thesis_case_dispatch/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/README.md
tags: [pressure-ledger, negative-k, section-effective, thesis-handoff]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - .agent/status/2026-07-21_TODO-NEGATIVE-K-SECTION-EFFECTIVE-THESIS-CASE-DISPATCH-2026-07-21.md
task: TODO-NEGATIVE-K-SECTION-EFFECTIVE-THESIS-CASE-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Tester/Reviewer
type: operational_note
status: complete
---
# Negative-K Section-Effective Thesis Case Dispatch

## Why This Avenue Exists

The current `corner_lower_right` two-tap rows repeatedly failed ordinary
component-K admission, but the failure is scientifically useful. The literature
review shows that negative source-defined pressure coefficients can be basis or
recovery artifacts, while the CFD evidence shows hydrostatic dominance,
material reverse flow, missing straight/developing reference, missing
component isolation, and missing same-QOI UQ.

The objective is therefore to stop current component-K forcing and make the
negative result usable in the thesis as a model-form argument for
`Delta_p_recirc_section`.

## Open These First

1. `work_products/2026-07/2026-07-21/2026-07-21_negative_k_section_effective_thesis_case_dispatch/README.md`
2. `work_products/2026-07/2026-07-21/2026-07-21_negative_k_section_effective_thesis_case_dispatch/case_memo.md`
3. `work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/three_level_score.csv`
4. `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv`
5. `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv`

## Trusted Packages

- LitRev pressure/model-form extraction for naming and basis rules.
- LitRev pressure-corner basis recovery for sign-safe decomposition.
- Pressure-corner publication freeze for canonical claims.
- Two-tap section-effective hybrid pressure scorecard for current residual
  values and no-refit diagnostic performance.

## Active Board Rows

- `TODO-NEGATIVE-K-SECTION-EFFECTIVE-THESIS-CASE-DISPATCH-2026-07-21`
  owns this consolidation and closeout.
- `TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21`
  is the proposed thesis insertion row.
- `TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21`
  is the proposed performance/baseline comparison row.

## Next Task Sequence

1. Run the thesis insertion row after exact thesis files are clear.
2. Run the no-fit bakeoff row if F3/Shah apparent baseline artifacts are
   source-resolved and train-only split boundaries are clear.
3. Keep ordinary component-K work closed for current rows unless new
   low-recirculation/nonrecirculating anchors and same-QOI UQ are introduced by
   a separate task.

## Output Contract

Use the words `section-effective pressure residual`,
`pressure-recovery diagnostic`, and `Delta_p_recirc_section`. Preserve the
negative sign. Do not say the current rows admit component `K`, cluster `K`,
F6, validation performance, holdout performance, external-test generalization,
or a predictive candidate.

## Do-Not-Do Guardrails

Do not clip the negative residual, fit a hidden multiplier, absorb the residual
into internal `Nu`, score protected split rows, change Fluid, mutate native CFD
outputs, mutate registry/admission state, or use the failed current corner rows
as F6 evidence.
