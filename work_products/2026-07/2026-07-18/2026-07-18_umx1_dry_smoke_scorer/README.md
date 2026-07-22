---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
tags: [umx1, forward-predictive, smoke, no-admission]
related:
  - .agent/status/2026-07-18_AGENT-544.md
  - .agent/journal/2026-07-18/umx1-dry-smoke-scorer.md
task: AGENT-544
date: 2026-07-18
role: Implementer/Tester/Writer
type: work_product
status: fast_scan_smoke_complete
---

# UMX1 Dry/Smoke Scorer

Generated: `2026-07-18T20:39:12+00:00`

## Result

Status: `fast_scan_smoke_complete`.

This package uses the AGENT-540 Fluid UMX1 API as a smoke scorer only. It checks
runtime legality, split discipline, accepted roots, and UMX energy conservation.
It does not fit, tune, select, or admit a candidate.

## Contract

- Candidates: `UMX1_disabled_baseline`, `UMX1_exchange_0p01`,
  `UMX1_exchange_0p05`.
- Executable smoke cases: Salt2, Salt3, Salt4 nominal from the current
  predictive input contract.
- Salt1: explicitly blocked until schema promotion, per canonical final split
  policy.
- Runtime: predictive air-side HX only; no imposed cooler duty, CFD mdot,
  realized wallHeatFlux, or TP/TW targets before solve.

## Outputs

- `umx1_candidate_definitions.csv`
- `umx1_case_split_contract.csv`
- `umx1_scenario_contracts.csv`
- `umx1_runtime_input_audit.csv`
- `umx1_smoke_results.csv`
- `umx1_root_status_by_case.csv`
- `umx1_segment_ledger.csv`
- `umx1_conservation_ledger.csv`
- `umx1_probe_smoke_score.csv`
- `umx1_no_admission_review.csv`

## Summary

- Planned smoke rows: `9`.
- Completed smoke rows: `9`.
- Root pass rows: `3/9`.
- Conservation pass rows: `9/9`.
- Expansion status: `stop_before_grid`.
- Admission status: `not_admitted_smoke_only`.
