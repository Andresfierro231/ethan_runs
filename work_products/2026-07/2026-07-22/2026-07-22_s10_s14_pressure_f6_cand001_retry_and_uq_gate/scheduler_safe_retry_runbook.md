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

# Scheduler-Safe CAND-001 Retry Runbook

## Decision

Create a future, separately claimed scheduler retry row for CAND-001 only if the scientific owner still wants the high-heat/no-recirculation source family. Do not launch from this gate.

## Why Retry Is Warranted

The previous CAND-001 jobs ended in Slurm `TIMEOUT`, not a physics rejection. The timeout evidence means terminal source cases are missing; it does not prove the candidate cannot become a low-recirculation anchor.

## Why Scoring Is Not Warranted

Current CAND-001 endpoint fields are not terminal-ready, ordinary-flow candidate pairs are zero, same-QOI mesh/time UQ has zero admissible rows, and F3-vs-F6 comparison is not evaluated. Therefore there is no F6 fit, no component K, no cluster K, no clipped K, and no hidden multiplier.

## Future Retry Row Must Do

1. Verify no duplicate CAND-001 retry job is active.
2. Name exact source cases, restart times, processor layout, walltime, allocation, logs, and expected terminal condition.
3. Run only under scheduler control, not as a detached login-node process.
4. After terminal success, emit endpoint field readiness for `p`, `p_rgh`, `U`, `rho`, `T`, face area, face normal, static and p_rgh deltas, hydrostatic and kinetic corrections, local dynamic pressure, RAF, RMF, and SVF.
5. Stop before F6 scoring unless ordinary-flow and same-QOI UQ gates pass in a later row.

## Fallback

If CAND-001 compute is deferred, audit CAND-002 corrected +/-10Q terminal readiness before any new CAND-001 submission.
