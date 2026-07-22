---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_parallel_execution_coordination/h1_feasibility_notes.csv
tags: [forward-model, predictive-1d, hydraulics, h1-proxy]
related:
  - .agent/status/2026-07-13_AGENT-308.md
  - .agent/journal/2026-07-13/predictive-h1-proxy-rerun.md
task: AGENT-308
date: 2026-07-13
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Predictive H1 Proxy Rerun

Generated: `2026-07-13T22:46:57+00:00`

This package runs an `ethan_runs`-only H1-like hydraulic screen. It is not
a faithful localized H1 implementation because current Fluid only accepts
aggregate `MinorLosses` fixed-K controls.

## Result

- Aggregate Salt2 train finite fit-target `K_local` sum: `40.6384`.
- Accepted rows: `6` of `6`.
- Thermal fitting used: `false`.
- Publication closure allowed: `false`.

## Outputs

- `h1_proxy_run_plan.csv`
- `h1_proxy_results.csv`
- `h1_proxy_variant_summary.csv`
- `h1_proxy_k_source.csv`
- `summary.json`

## Guardrail

Use this only as a directionality screen. Faithful localized H1 still needs
Fluid-side named/localized hydraulic-loss and reset metadata support.
