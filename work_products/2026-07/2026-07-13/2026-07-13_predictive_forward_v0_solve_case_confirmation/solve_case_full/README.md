# Predictive Forward V0: Imposed Cooler

Generated: `2026-07-13T22:28:41+00:00`

This package runs Fluid's pressure-rooted forward solve with heater setup input
and imposed cooler duty. It does not use CFD mdot, CFD realized wallHeatFlux, or
sensor temperatures as runtime inputs.

## Variants

- `F0_current_fluid_sources`: current Fluid salt source contract, heater plus
  configured 37 W test-section input.
- `F1_heater_only`: heater setup power only; test-section source omitted until
  the heater/test-section transfer contract is resolved.

Both variants use `model_mode=imposed_qhx`, radiation off, 1.0 in insulation,
and case-specific CFD boundary Ta when available.

## Result Snapshot

Engine: `solve_case`.

- `F0_current_fluid_sources`: mean abs Tmean error `34.377 K`, mean mdot error vs CFD `0.007836 kg/s`, mean ambient loss `185.151 W`, max abs pressure residual `0.000 Pa`.
- `F1_heater_only`: mean abs Tmean error `4.610 K`, mean mdot error vs CFD `0.005358 kg/s`, mean ambient loss `148.151 W`, max abs pressure residual `0.000 Pa`.

The heater-only source contract is much closer on CFD mean temperature in this
first pass, but both variants overpredict mdot. Treat this as progress on
thermal source/sink matching, not hydraulic validation.

## Files

- `forward_v0_run_plan.csv`: run matrix and runtime policy.
- `forward_v0_results.csv`: mdot, thermal proxy, pressure, and heat-ledger
  outputs with CFD/experimental targets joined only as scores.
- `forward_v0_sensor_predictions_experimental.csv`: Fluid experimental TP/TW
  validation stream.
- `forward_v0_sensor_predictions_cfd.csv`: CFD sensor-reference stream when
  current references expose matching sensor names.
- `forward_v0_segment_states.csv`: segment-level 1D temperatures, sources,
  sinks, and heat-transfer diagnostics.
- `forward_v0_variant_summary.csv`: compact variant-level error and residual
  summary.
- `forward_v0_input_audit.csv`: consumed runtime fields mapped back to the
  strict input contract.
- `forward_v0_litrev_gate_reference_audit.csv`: required pre-score lit-rev gate
  references for source envelope, property mode lane, named losses, heat-loss
  admission, and CFD coefficient naming limits.
- `summary.json`: machine-readable package summary.

## Interpretation

This is not an end-to-end HX prediction yet. It is the practical next bridge:
given physical setup inputs and imposed cooler duty, solve mdot and temperatures
without anchoring to CFD mdot or measured sensors. Remaining blockers are HX
UA/epsilon-NTU, heater/test-section transfer efficiency, wall-layer temperature
mapping, hydraulic gate status, thermal mesh uncertainty, and sensor-coordinate
uncertainty.

Scoring is blocked unless the input contract carries explicit references to the
five lit-rev gate outputs. The current package writes those references to
`forward_v0_litrev_gate_reference_audit.csv` before emitting score tables.

The default `fast_scan` engine uses Fluid `pressure_residual` evaluations on a
bounded mdot grid plus a short bracketed bisection. Run the same script with
`--engine solve_case` on an appropriate compute node for the full nested Fluid
root solve.
