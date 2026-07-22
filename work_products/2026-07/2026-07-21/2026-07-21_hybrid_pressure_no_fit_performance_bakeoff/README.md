---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/section_effective_pressure_scorecard.csv
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/three_level_score.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/f3_comparison_status.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/f3_vs_f6_comparison_readiness.csv
tags: [pressure-ledger, hybrid-pressure, no-fit, bakeoff, thesis]
related:
  - .agent/status/2026-07-21_TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21.md
  - .agent/journal/2026-07-21/hybrid-pressure-no-fit-performance-bakeoff.md
  - imports/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff.json
task: TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Tester/Writer
type: work_product
status: complete
---
# Hybrid Pressure No-Fit Performance Bakeoff

## Result

This package tests the section-effective hybrid pressure route without fitting,
tuning, protected split scoring, or model selection. It compares observed
decomposition, Salt2-frozen diagnostic transfer, oracle upper bound, and the
available F3/Shah apparent baseline status.

The Salt2-frozen diagnostic transfer remains the only numeric transfer check.
Its max all-row and Salt3/Salt4 transfer absolute error is
`0.47046606946166093438399 Pa`.

F3/Shah apparent baseline comparison is not numeric here. The existing F3/F6
artifacts record `not_evaluated_no_ordinary_candidate`; no ordinary admissible
F6 row exists for a fair F3-vs-F6 comparison.

## Decision

The current hybrid pressure term is thesis evidence only. It is useful for
residual ownership and model-form motivation, but it is not candidate-reviewable
for freeze/admission from current rows.

## Outputs

- `no_fit_performance_table.csv`
- `residual_ownership_table.csv`
- `baseline_comparison_provenance.csv`
- `split_role_audit.csv`
- `candidate_reviewability_decision.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, validation/holdout/external score, fitting, tuning,
model selection, component-K/F6/cluster-K admission, clipped K, hidden/global
multiplier, S11/S15/S6 trigger, blocker register, generated index, mixed-basis
promotion, or thesis current file is changed by this package.
