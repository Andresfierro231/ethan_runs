---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/tested_model_form_sensor_errors.csv
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment/source_basis_coverage.csv
tags: [model-form, d4, segment-source-placement, source-bounded-gate, thesis]
related:
  - .agent/status/2026-07-22_TODO-MF-D4-SEGMENT-SOURCE-PLACEMENT-EVIDENCE-GATE-2026-07-22.md
  - .agent/journal/2026-07-22/mf-d4-segment-source-placement-evidence-gate.md
task: TODO-MF-D4-SEGMENT-SOURCE-PLACEMENT-EVIDENCE-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Tester / Writer / Reviewer
type: work_product
status: complete
---
# D4 Segment Source-Placement Evidence Gate

This package tests whether the best diagnostic residual form,
`D4_M3_segment_offsets_min2_train`, can be explained by independent
source/geometry evidence. It does not fit a new model, release source/property
terms, execute a repair, or admit D4.

## Decision

`D4` remains an empirical upper-bound diagnostic. No source-bounded local
source-placement candidate is ready for freeze review.

The evidence is useful: D4 reduced transfer RMSE to
`7.9404 K`, a
`54.2723 %` reduction versus
M3. But the independent source/property and geometry release gates remain
closed for all target segments.

## Outputs

- `segment_residual_map.csv`
- `independent_source_heat_path_evidence.csv`
- `runtime_legality_matrix.csv`
- `source_bounded_candidate_gate.csv`
- `publication_claim_boundary.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
