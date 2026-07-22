# Predictive Input Contract

Generated: `2026-07-13T21:10:48+00:00`

This package defines the runtime-input guardrail for the next pressure-rooted
forward 1D model slice.

## What Is Allowed

- `forward_v0_imposed_cooler` may use physical setup inputs, declared Fluid
  geometry/properties, heater setup power, no-radiation scenario control,
  insulation setup, ambient/Ta setup, and imposed cooler duty.
- `predictive_hx` must not use imposed cooler duty; it remains blocked until a
  low-dimensional UA or epsilon-NTU model is fit and validated.

## What Is Forbidden At Runtime

The forward solver must not consume CFD mdot, CFD mean/delta temperatures,
realized CFD wallHeatFlux, experimental TP/TW measurements, or CFD sensor
references. Those fields are validation or diagnostic evidence and are joined
only after the solve.

## Files

- `runtime_input_contract.csv`: field-level classes and runtime permissions.
- `mode_contract.csv`: mode-level allowed/forbidden input policy.
- `case_runtime_inputs_forward_v0.csv`: Salt 2-4 runtime input rows for the
  imposed-cooler forward-v0 runner.
- `validation_target_contract.csv`: validation and diagnostic fields to join
  after solving.
- `violations.csv`: strict-contract violations; expected to be empty.
- `summary.json`: machine-readable package metadata.

## Current Boundaries

This is predictive only conditional on imposed cooler duty. It does not solve
the HX boundary yet, does not fit heater transfer efficiency, and does not admit
thermal mesh-sensitive h/Nu/UA corrections.

Before any forward-v0 score is treated as meaningful, the runtime contract must
carry five lit-rev gate references: source envelope, property mode lane,
named-loss table, heat-loss admission table, and CFD coefficient naming limits.
