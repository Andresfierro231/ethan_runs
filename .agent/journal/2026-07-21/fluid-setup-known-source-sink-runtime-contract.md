---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
tags: [journal, fluid, setup-known-source, heater-source]
related:
  - .agent/status/2026-07-21_TODO-FLUID-SETUP-KNOWN-SOURCE-SINK-RUNTIME-CONTRACT-2026-07-21.md
task: TODO-FLUID-SETUP-KNOWN-SOURCE-SINK-RUNTIME-CONTRACT-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer
type: journal
status: complete
---
# Setup-Known Source/Sink Runtime Contract

## Attempted

Checked the source/sink provenance recovery package and the external Fluid
solver API for a legal lower-leg heater source path.

## Observed

Salt2 lower-leg heater setup Q is `265.7 W` from staged `0/T` setup files.
Fluid already exposes `ScenarioConfig.heater_source_mode` with supported value
`tw4_to_tp3_three_span`, default weights `0.45/0.35/0.20`, and span bounds
`TW4-TW5`, `TW5-TW6`, and `TW6-TP3`.

## Inferred

No external Fluid source edit is needed to perform the next train-only source
effect test. The API is executable, but the source lane is not admitted for
runtime scoring, source/property release, or freeze.

## Caveats

This package does not prove thermal predictivity. It only separates a legal
setup-known source contract from forbidden realized-output shortcuts.

## Next Useful Action

Run the train-only residual decomposition row with
`heater_source_mode=tw4_to_tp3_three_span` and compare TW4-TW6 against Phase E.
