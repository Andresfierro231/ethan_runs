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

# S10/S14 Pressure F6 CAND-001 Retry And UQ Gate

Task: `TODO-S10-S14-PRESSURE-F6-CAND001-RETRY-AND-UQ-GATE-2026-07-21`

Decision: `cand001_retry_runbook_recommended_no_launch_no_f6_scoring`

This package decides retry/no-retry for CAND-001 and writes a scheduler-safe future runbook. It does not launch compute, harvest endpoints, fit F6, admit component K, or compare F3 against F6.

## Outputs

- `timeout_source_ordinary_uq_gate_matrix.csv`: terminal/source/ordinary-flow/UQ gates.
- `retry_decision.csv`: retry/no-retry decision and claim boundary.
- `scheduler_safe_retry_runbook.md`: future scheduler row requirements.
- `endpoint_field_requirement_table.csv`: fields required before endpoint use.
- `f3_vs_f6_comparison_prerequisites.csv`: comparison is blocked until an admissible F6 row exists.
- `lower_right_negative_result_classification.csv`: lower-right result is section-effective/diagnostic only.
- `s11_decision.csv`: S11/S15/S6 remain blocked.

## Core Scientific Boundary

The lower-right pressure rise is hydrostatic/recovery/section-effective diagnostic evidence, not negative loss and not component-K/F6 evidence. CAND-001 is retryable as source recovery only; the current pressure closure path remains unadmitted.
