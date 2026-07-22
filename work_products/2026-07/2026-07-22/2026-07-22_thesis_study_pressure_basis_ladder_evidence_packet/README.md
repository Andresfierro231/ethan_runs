---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/section_effective_pressure_scorecard.csv
  - work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/no_fit_performance_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/timeout_source_ordinary_uq_gate_matrix.csv
tags: [thesis, pressure, f6, section-effective, negative-result]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-PRESSURE-BASIS-LADDER-EVIDENCE-PACKET-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-study-pressure-basis-ladder-evidence-packet.md
  - imports/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet.json
task: TODO-THESIS-STUDY-PRESSURE-BASIS-LADDER-EVIDENCE-PACKET-2026-07-22
date: 2026-07-22
role: Hydraulics/Writer/Reviewer/Tester
type: work_product
status: complete
---
# Thesis Pressure Basis Ladder Evidence Packet

## Result

Decision: `pressure_basis_ladder_packet_ready_thesis_evidence_only`.

This package prepares pressure negative-result evidence for external thesis
writing. It does not admit component `K`, cluster `K`, F6, clipped `K`, a hidden
multiplier, or a frozen candidate.

- section-effective rows: `3`
- negative signed residual rows: `3`
- component-K admitted rows: `0`
- F6 fit rows: `0`
- F3/F6 numeric comparison released: `False`
- Salt2-frozen diagnostic transfer max absolute error:
  `0.47046606946166093438399 Pa`

## Interpretation

The current lower-right two-tap rows are useful because they quantify the
failure mode. Gross static pressure rise is hydrostatic dominated. After
hydrostatic and kinetic correction, Salt2/Salt3/Salt4 have small negative
section-effective residuals. Those residuals motivate a
throughflow-plus-recirculation term, `Delta_p_recirc_section`, but they do not
support ordinary component-K or F6 admission.

F3/Shah-vs-F6 remains not evaluated numerically. The current F6 path lacks an
ordinary-flow candidate, finite endpoint evidence, same-QOI UQ, source/property
release, and a frozen split-safe candidate.

## Outputs

- `pressure_basis_ladder.csv`
- `section_effective_residual_values.csv`
- `pressure_non_admission_gate_matrix.csv`
- `f3_f6_and_hybrid_comparison_status.csv`
- `thesis_pressure_claim_boundary.csv`
- `figure_table_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Thesis Claim Boundary

Allowed: the pressure basis ladder and signed residuals are thesis evidence for
why the hybrid pressure model is needed.

Forbidden: do not force a component `K`, clip negative residuals, infer an
ordinary single-stream loss, claim F6 admission, claim F3/Shah was beaten
numerically, or use these rows as validation/holdout/external-test evidence.
