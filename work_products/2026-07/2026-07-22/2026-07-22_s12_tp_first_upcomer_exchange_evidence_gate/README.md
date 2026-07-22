---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/finite_train_metric_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/s13_exchange_trend_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/production_readiness_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch/signed_error_shape_metrics.csv
tags: [s12, tp-first, upcomer-exchange, diagnostic-only]
related:
  - .agent/status/2026-07-22_TODO-S12-TP-FIRST-UPCOMER-EXCHANGE-EVIDENCE-GATE-2026-07-22.md
  - operational_notes/07-26/22/2026-07-22_S12_TP_FIRST_UPCOMER_EXCHANGE_EVIDENCE_GATE.md
task: TODO-S12-TP-FIRST-UPCOMER-EXCHANGE-EVIDENCE-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Hydraulics / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S12 TP-First Upcomer Exchange Evidence Gate

Decision: `tp_first_s12_exchange_continuation_diagnostic_only`.

This package continues S12 scientifically, but reframes the next useful work
around TP rather than TW-only residual ownership. The available evidence says:

- S12-HIAX1 has finite train-only TP/TW/mdot/pressure context, but remains not
  frozen.
- Current M3 TP RMSE is lower than TW RMSE across Salt2/Salt3/Salt4, but TP is
  still cold-biased and is a valid thesis-priority QOI.
- S13 retained-window exchange proxies are finite for Salt2/Salt3/Salt4 and
  are directly relevant to TP through residence time, core/bulk temperature,
  pressure, and source-side energy balance.
- Production harvest, same-QOI UQ, source/property release, final score, and
  freeze are still closed.

Primary files:

- `s12_tp_priority_context.csv`
- `s12_hiax1_train_only_context.csv`
- `s12_tp_exchange_evidence_table.csv`
- `s12_tp_unlock_gate_matrix.csv`
- `s12_tp_next_executable_queue.csv`
- `s12_tp_claim_boundary.csv`
- `figures/svg/s12_tp_first_exchange_status.svg`

Guardrails: no protected split scoring, no source/property or new
Qwall release, no candidate freeze, no final score, no scheduler action, no
native-output mutation, and no residual absorption into internal Nu.
