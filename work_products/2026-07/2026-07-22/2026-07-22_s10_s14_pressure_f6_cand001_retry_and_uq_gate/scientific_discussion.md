---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_low_recirc_source_readiness/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s5_source_property_split_release/summary.json
tags: [pressure, f6, cand001, same-qoi-uq, thesis, publication-evidence]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/scheduler_safe_retry_runbook.md
task: TODO-S10-S14-PRESSURE-F6-CAND001-RETRY-AND-UQ-GATE-2026-07-21
date: 2026-07-22
role: Hydraulics / cfd-pp / Scheduler / Tester / Writer / Reviewer
type: work_product
status: complete
---

# Scientific Discussion

## Observed Result

The lower-right pressure-corner result is a negative pressure-admission result. The gross static pressure rise is hydrostatic dominated, the available signed residual is small and negative, and the rows fail ordinary-flow, component-isolation, same-basis straight-reference, and same-QOI UQ gates.

## Interpretation

The lower-right rows may be cited as section-effective pressure residual and pressure-recovery diagnostic evidence. They must not be renamed as negative loss coefficients, component-K evidence, cluster-K evidence, or F6 evidence.

## CAND-001 Decision

CAND-001 deserves a future scheduler-safe retry row because its current failure is timeout/source-terminal failure rather than a completed no-go physics result. That retry is only source recovery. It does not authorize endpoint sampling, F6 scoring, F3-vs-F6 comparison, S11 release, or S15/S6 trigger.

## Publication Boundary

The pressure path remains scientifically useful as a rigorous blocked gate. A publication can state exactly why pressure rose around the corner and why that rise is not a negative loss. It cannot claim an admitted pressure closure.
