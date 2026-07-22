---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_low_recirc_anchor_design_and_harvest/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/summary.json
tags: [pressure, f6, ordinary-basis, negative-result, thesis-evidence]
related:
  - .agent/status/2026-07-22_TODO-THESIS-PRESSURE-F6-ORDINARY-BASIS-FAILURE-PACKET-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-pressure-f6-ordinary-basis-failure-packet.md
  - imports/2026-07-22_thesis_pressure_f6_ordinary_basis_failure_packet.json
task: TODO-THESIS-PRESSURE-F6-ORDINARY-BASIS-FAILURE-PACKET-2026-07-22
date: 2026-07-22
role: Hydraulics / cfd-pp / Writer / Reviewer / Tester
type: work_product
status: complete
---
# Pressure F6 Ordinary-Basis Failure Packet

Decision: `pressure_f6_ordinary_basis_failure_packet_ready_no_component_k_no_f6_admission`.

This packet gives the thesis a clean negative result: the lower-right two-tap
rows are usable as section-effective pressure residual evidence, but they must
not be forced into component `K`, cluster `K`, F6, clipped `K`, hidden
multiplier, or F3/Shah comparison claims.

The current evidence is consistent:

- `3` lower-right section-effective rows exist.
- `3` signed residuals are negative and small relative to gross hydrostatic
  pressure rise.
- `0` component-K rows are admitted.
- `0` F6 fit rows are admitted.
- `0` ordinary candidate pairs exist now.
- `0` same-QOI mesh/time UQ rows are admissible.
- CAND001 terminal source success is `0` after `2` timeout jobs.

The publishable conclusion is that pressure remains hydrostatic-dominated in
the two-tap corner rows, while the residual is a diagnostic reason to prefer a
future throughflow-plus-recirculation or section-effective pressure model over
ordinary component-K extraction from those rows.
