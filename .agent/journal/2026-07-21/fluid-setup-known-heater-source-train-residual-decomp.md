---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp/train_metric_comparison.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp/tw4_tw6_focus.csv
tags: [journal, fluid, setup-known-source, residual-decomposition]
related:
  - .agent/status/2026-07-21_TODO-FLUID-SETUP-KNOWN-HEATER-SOURCE-TRAIN-RESIDUAL-DECOMP-2026-07-21.md
task: TODO-FLUID-SETUP-KNOWN-HEATER-SOURCE-TRAIN-RESIDUAL-DECOMP-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer
type: journal
status: complete
---
# Setup-Known Heater Source Train Residual Decomposition

## Attempted

Ran one bounded local Fluid `solve_case` for Salt2 train/support using the
existing Phase E external-boundary role rows plus
`heater_source_mode=tw4_to_tp3_three_span`.

## Observed

The solve completed with `root_status=accepted`. TW6 improved by `1.801 K` in
absolute residual, but TW4 and TW5 worsened. Aggregate all-probe MAE increased
slightly from `81.5815 K` to `81.6506 K`.

## Inferred

The setup-known source lane is executable, but it is not sufficient by itself
to explain the heated-incline residual. The result supports the earlier audit:
source treatment matters, but a model-form deficiency remains.

## Caveats

This is train-only diagnostic evidence. It does not release source/property
labels, freeze a candidate, admit a closure, or score validation/holdout/external
rows.

## Next Useful Action

Use this as a fail-closed source-lane effect test and move to one predeclared
model-form candidate only after board coordination: axial mixing or
upcomer/heated-incline exchange.
