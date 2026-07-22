---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/candidate_anchor_inventory.csv
  - work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/harvest_readiness_queue.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement/terminal_status_refresh.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/endpoint_sampling_contract.csv
tags: [pressure-corner, low-recirculation-anchor, two-tap, cfd-pp]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_same_qoi_scientific_synthesis/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/README.md
task: TODO-PRESSURE-CORNER-LOW-RECIRC-ANCHOR-HARVEST
date: 2026-07-21
role: cfd-pp/Hydraulics/Tester/Writer
type: work_product
status: complete
---
# Pressure-Corner Low-Recirculation Anchor Preflight

## Result

This package implements the preflight part of the low-recirculation anchor
harvest. It does not launch a sampler, scheduler job, solver, postprocessor, F6
fit, or coefficient admission.

`CAND-001` remains the preferred source family: Salt4 high-heat/no-recirculation
probes. It is still blocked because the cited evidence does not provide a
terminal-success/harvest-ready state or endpoint raw fields for
`lower_leg__s04;right_leg__s00`.

## Files

- `candidate_terminal_preflight.csv`
- `source_case_readiness.csv`
- `endpoint_field_availability.csv`
- `anchor_decision.csv`
- `sampler_or_no_launch_decision.json`
- `source_manifest.csv`
- `summary.json`

## Next Action

Refresh terminal state for the high-heat `CAND-001` cases through a claimed
terminal-refresh or latest-CFD schema-promotion row. Only after terminal success
should a future staged-copy sampler row claim exact output paths and sample
endpoint fields.

## Guardrails

No ordinary component-K review is queued until same-window aggregate `RAF <
0.01` and `RMF < 0.01` are measured for the candidate endpoint. Raw rows alone
are not admission. Current Salt2/Salt3/Salt4 rows remain section-effective
diagnostics.
