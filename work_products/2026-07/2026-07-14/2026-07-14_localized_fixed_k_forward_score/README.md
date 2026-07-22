---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/forward_v0_results.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun/h1_proxy_k_source.csv
  - work_products/2026-07/2026-07-14/2026-07-14_fluid_localized_h1_and_boundary_api/README.md
tags: [forward-model, hydraulics, localized-fixed-k, scorecard]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_fluid_localized_h1_and_boundary_api/README.md
task: AGENT-328
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Localized Fixed-K Forward Score

Generated: `2026-07-14T17:07:05+00:00`

## Decision

This package executes the localized fixed-K work packet through the existing
Fluid hook. The current localized-only score does not pass the directional
hydraulic screen; it remains diagnostic-only for final forward-v1 because the
run still uses imposed cooler duty and does not implement reset/redevelopment
semantics.

`F1_heater_only` localized fixed-K mean mdot error is `0.005894 kg/s`, with mean reduction `-6.78%` vs baseline.

Final forward-v1 remains: `blocked_no_go_final_forward_v1_not_admitted`.

## Guardrails

- Thermal fitting used: `false`.
- Runtime CFD mdot used: `false`.
- Runtime realized CFD wallHeatFlux used: `false`.
- Runtime validation temperatures used: `false`.
- Runtime imposed cooler duty used: `true`, so this is not final setup-only
  boundary/HX evidence.
- Global hydraulic multiplier exported: `false`.

## Outputs

- `localized_fixed_k_source.csv`
- `localized_fixed_k_scorecard.csv`
- `localized_fixed_k_variant_summary.csv`
- `rigor_gate_audit.csv`
- `source_manifest.csv`
- `summary.json`
