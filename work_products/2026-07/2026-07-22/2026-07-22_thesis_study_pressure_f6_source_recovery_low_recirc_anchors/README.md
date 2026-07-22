---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/summary.json
tags: [pressure, f6, cand001, low-recirculation-anchor, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-PRESSURE-F6-SOURCE-RECOVERY-LOW-RECIRC-ANCHORS-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-study-pressure-f6-source-recovery-low-recirc-anchors.md
task: TODO-THESIS-STUDY-PRESSURE-F6-SOURCE-RECOVERY-LOW-RECIRC-ANCHORS-2026-07-22
date: 2026-07-22
role: Hydraulics / cfd-pp / Scheduler / Tester / Writer / Reviewer
type: work_product
status: complete
---
# Pressure F6 Source Recovery / Low-Recirculation Anchors

Decision: `monitor_only_cand001_running_no_f6_recovery_yet`.

This packet updates the pressure F6/source-recovery path without submitting,
harvesting, fitting, or admitting anything. A read-only scheduler check on
2026-07-22 found CAND001 job `3308712` still running, so terminal-source
recovery cannot proceed yet.

## Result

- CAND001 remains the preferred low-recirculation anchor lane.
- Current terminal-ready CAND001 source cases: `0`.
- Current endpoint fields ready for F6 review: `0`.
- Ordinary candidate pairs ready: `0`.
- Same-QOI mesh/time UQ admissible rows: `0`.
- F6 fit rows: `0`.
- Component-K, cluster-K, clipped-K, and hidden multiplier admissions: `0`.
- Lower-right two-tap rows remain section-effective diagnostic evidence, not
  component-K or F6 evidence.

## Outputs

- `source_manifest.csv`
- `scheduler_observation.csv`
- `cand001_terminal_source_state.csv`
- `low_recirc_anchor_map.csv`
- `pressure_basis_ladder_update.csv`
- `f6_admission_waterfall.csv`
- `post_terminal_action_contract.csv`
- `figure_table_targets.csv`
- `summary.json`

## Stop/Go Rule

Do not run F3/Shah-vs-F6 comparison, F6 fitting, component-K admission, or S11/S15/S6
triggering until CAND001 is terminal-successful and a later row verifies
steady-state drift, endpoint static-pressure fields, low recirculation, same-QOI
time/mesh UQ, source/property legality, and ordinary-flow/component-isolation
requirements.
