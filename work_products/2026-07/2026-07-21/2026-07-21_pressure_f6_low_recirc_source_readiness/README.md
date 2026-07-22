---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/candidate_terminal_preflight.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/source_case_readiness.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/f6_gate_refresh.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design/summary.json
tags: [pressure, f6, low-recirculation, source-readiness, no-admission]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-F6-LOW-RECIRC-SOURCE-READINESS-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design/README.md
task: TODO-PRESSURE-F6-LOW-RECIRC-SOURCE-READINESS-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: work_product
status: complete
---
# Pressure/F6 Low-Recirculation Source Readiness

## Decision

No F6 sampler or coefficient review is allowed now. The refreshed evidence still
has `0` terminal-ready low-recirculation source cases and `0` ordinary-flow F6
candidate pairs.

`CAND-001` remains the preferred high-heat/no-recirculation source family, but
the current read-only scheduler observation is split: job `3299610` timed out,
while job `3299620` is still running. Endpoint fields remain unavailable until a
terminal staged-copy sampler is separately claimed.

## Open First

1. `summary.json`
2. `candidate_terminal_refresh.csv`
3. `source_case_readiness_refresh.csv`
4. `endpoint_field_readiness.csv`
5. `ordinary_flow_evidence_inventory.csv`
6. `sampler_go_no_go.csv`
7. `next_task_queue.csv`

## Scientific Boundary

The current pressure/F6 publication claim freeze remains unchanged: pressure
rise around corners is hydrostatic/recovery/section-effective/diagnostic
evidence, not negative loss, and present F6 evidence is diagnostic-only.

The completed S13 same-window UQ design is useful parallel infrastructure but
does not release exchange-cell harvest, S11 review, or ordinary F6 scoring.

## Guardrails

No native output, registry/admission state, scheduler state, solver,
postprocessor, sampler, harvest output, Fluid/external repo, blocker register,
generated index, manuscript file, fitting/model selection, F6 fit, component
`K`, cluster `K`, clipped `K`, or hidden/global multiplier was changed or
produced.
