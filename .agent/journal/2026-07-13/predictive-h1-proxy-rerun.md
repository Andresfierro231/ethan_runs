---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_parallel_execution_coordination/h1_feasibility_notes.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv
tags: [forward-model, predictive-1d, hydraulics, h1-proxy]
related:
  - .agent/status/2026-07-13_AGENT-308.md
  - imports/2026-07-13_predictive_h1_proxy_rerun.json
task: AGENT-308
date: 2026-07-13
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Predictive H1 Proxy Rerun

## Observed

AGENT-299 identified H1 as the next hydraulic path but also documented that a
faithful localized H1 implementation requires Fluid-side API work. Current Fluid
accepts aggregate `MinorLosses`, not named localized component/cluster/branch
losses with reset metadata.

## Implemented

Added `tools/analyze/run_predictive_h1_proxy_rerun.py` and
`tools/analyze/test_predictive_h1_proxy_rerun.py`.

The runner:

- uses only Salt2 train finite `fit_target` `K_local` rows from the named-loss
  table;
- sums those rows into one aggregate fixed-K proxy (`40.63836886473942`);
- runs Salt2/Salt3/Salt4 for both forward-v0 source variants;
- keeps `thermal_fit_used=false` and `publication_closure_allowed=false`.

## Interpretation

The proxy moved mdot in the intended direction. For the heater-only source
variant, mean mdot error vs CFD dropped to `0.002144166666666668 kg/s` in the
screen. This is useful evidence that added hydraulic resistance is directionally
promising, but it is not a thesis-grade localized H1 closure because the named
losses have been collapsed into one fixed-K control.

## Validation

- `python3 -m py_compile tools/analyze/run_predictive_h1_proxy_rerun.py tools/analyze/test_predictive_h1_proxy_rerun.py`
- `python3 -m unittest tools.analyze.test_predictive_h1_proxy_rerun`
- `python3 tools/analyze/run_predictive_h1_proxy_rerun.py`

All passed. No external Fluid source, native CFD output, registry, or scheduler
state was modified.
