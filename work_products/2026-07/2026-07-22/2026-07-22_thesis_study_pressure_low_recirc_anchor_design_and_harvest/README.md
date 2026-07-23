---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory/anchor_inventory_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory/sampled_endpoint_ordinary_flow_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_alternate_low_reverse_anchor_screen/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_alternate_low_reverse_anchor_screen/disqualification_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/pressure_basis_ladder.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/timeout_source_ordinary_uq_gate_matrix.csv
tags: [pressure, f6, low-recirculation, anchor-design, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-PRESSURE-LOW-RECIRC-ANCHOR-DESIGN-AND-HARVEST-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-study-pressure-low-recirc-anchor-design-and-harvest.md
  - imports/2026-07-22_thesis_study_pressure_low_recirc_anchor_design_and_harvest.json
task: TODO-THESIS-STUDY-PRESSURE-LOW-RECIRC-ANCHOR-DESIGN-AND-HARVEST-2026-07-22
date: 2026-07-22
role: Hydraulics / cfd-pp / Scheduler / Writer / Reviewer / Tester
type: work_product
status: complete
---
# Pressure Low-Recirculation Anchor Design And Harvest Gate

Decision: `fail_closed_no_existing_reviewable_low_recirc_pressure_anchor_no_scheduler_launch`.

This package audits whether any existing CFD/postprocessed pressure evidence can
serve as a nonrecirculating or low-reverse-flow anchor for F3/F6/component-K
admission. It also converts the negative result into a precise future compute
and harvest contract.

## Result

No current row is reviewable for F6 or component-K admission.

- Low/nonrecirculating anchor inventory reviewed `36` candidate rows.
- Preferred future ordinary anchor rows: `6`.
- Sampled endpoint ordinary-flow pass rows: `0`.
- F6 fit-ready rows now: `0`.
- Alternate screen rows: `40`.
- Existing replacement-ready rows: `0`.
- PM5 material reverse-flow rows: `12`.
- PM10 strong-recirculation rows: `4`.
- Same-QOI admissible mesh/time UQ rows: `0`.
- CAND-001 terminal success cases: `0`; timeout jobs: `2`.
- Lower-right section-effective pressure rows preserved: `3`; component-K rows:
  `0`.

## Scientific Boundary

The lower-right two-tap evidence is useful as section-effective residual
evidence. It is not a component `K`, F6, Shah-comparison, clipped negative `K`,
or hidden multiplier basis. Gross static pressure rise is hydrostatic dominated,
and the remaining signed residual is small/negative after hydrostatic and
kinetic correction. That residual motivates a throughflow-plus-recirculation
term, not an ordinary single-stream loss coefficient.

## Package Files

- `anchor_absence_proof.csv`
- `candidate_span_inventory_summary.csv`
- `reverse_flow_screen_table.csv`
- `pressure_basis_compatibility.csv`
- `same_qoi_endpoint_uq_gate.csv`
- `minimum_future_harvest_runbook.csv`
- `figure_table_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
- `figures/svg/pressure_anchor_admission_gate_waterfall.svg`

## Next Gate

Do not submit compute from this row. The next scheduler-capable row must first
record the exact command contract. The most direct unlock is still a
scheduler-safe CAND-001 retry only if the scientific owner wants the high-heat/
no-recirculation source family. If compute is deferred, audit CAND-002 corrected
`+/-10Q` terminal readiness before CAND-001 resubmission.

After terminal success, endpoint harvest must emit finite `p`, `p_rgh`, `U`,
`rho`, `T`, face area, face normal, static and `p_rgh` deltas, hydrostatic and
kinetic corrections, local dynamic pressure, RAF, RMF, and SVF. Any ordinary
anchor row must pass RAF `< 0.01`, RMF `< 0.01`, endpoint-field readiness,
same-QOI same-formula same-sign time/mesh UQ, source/property/split labels, and
then a separate admission row.

## Validation

`python3.11 work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_low_recirc_anchor_design_and_harvest/check_pressure_low_recirc_anchor_packet.py` passes with:

`PASS pressure low-recirc anchor packet: 36 rows reviewed, 6 future anchors, 0 reviewable current anchors`.

## Guardrails

No scheduler launch, scheduler query/action, solver, postProcess, sampler,
harvest, UQ run, native-output mutation, registry/admission mutation, fitting,
model selection, source/property release, component-K/F6/Shah release, clipped
K, hidden multiplier, or final score was performed.
