# TODO-PATCHWISE-HEAT-LEDGER Status

Date: `2026-07-08`
Role: Implementer / Tester / Writer
Owner: codex

## Scope

Implemented the mechanistic Heat Sources/Sinks ledger requested after the
foundation pass. This now reconciles imposed thermal boundary duties,
wallHeatFlux integrals, segment enthalpy-flow changes, passive/junction losses,
residuals, sign convention, radiation availability, and the available
resistance-network terms for admitted Salt 2/3/4 Jin continuation rows.

## Context Read

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `.agent/status/2026-07-07_AGENT-194.md`
- `work_products/2026-07-07_heat_source_sink_ledger/README.md`
- `work_products/2026-07-07_heat_source_sink_ledger/summary.json`
- `work_products/2026-07-08_span_endpoint_temperatures/README.md`
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`

## Completed

- Extended `tools/analyze/build_patchwise_heat_ledger.py`.
- Extended `tools/analyze/test_patchwise_heat_ledger.py`.
- Regenerated `work_products/2026-07-08_patchwise_heat_ledger/`:
  - `patchwise_heat_ledger.csv`
  - `patchwise_heat_ledger.json`
  - `summary.json`
  - `README.md`
- Added ledger fields for:
  - heater imposed duty by patch group
  - cooler removed duty
  - passive wall heat leak/gain
  - junction loss
  - segment enthalpy-flow change
  - segment wallHeatFlux sum
  - wallHeatFlux-vs-enthalpy residual
  - BC type and sign convention
  - patch area, wall temperature, effective internal convection
  - wall conduction from `thicknessLayers`/`kappaLayerCoeffs`
  - external convection from BC `h`
  - external radiation marked absent unless a `qr` output term exists

## Observed Results

- `24` rows across Salt 2/3/4 Jin.
- Patch-group counts:
  - `ambient_wall`: 12
  - `cooler`: 3
  - `heater`: 3
  - `junction_other`: 3
  - `test_section`: 3
- Cooler imposed duty matches wallHeatFlux to within `0.001 W` in all three
  cases.
- Heater imposed duty exceeds realized wallHeatFlux:
  - Salt 2: `265.7 W` imposed vs `243.519 W` wallHeatFlux.
  - Salt 3: `297.5 W` imposed vs `273.155 W` wallHeatFlux.
  - Salt 4: `337.6 W` imposed vs `310.487 W` wallHeatFlux.
- Test-section BC remains a key contradiction: `37 W` imposed, but wallHeatFlux
  is a net sink:
  - Salt 2: `-5.68 W`
  - Salt 3: `-10.545 W`
  - Salt 4: `-16.769 W`
- No `qr` output term was found, so radiation is not included as an extracted
  heat ledger term despite emissivity metadata in the boundary condition.

## Interpretation

The Salt heat ledger is now mechanistic with respect to available OpenFOAM
outputs and BC metadata. It resolves the usable network legs:

- wallHeatFlux interface heat into/out of the fluid
- effective internal convection from reconstructed wall T minus bulk T
- wall/layer conduction from BC layer thickness and kappa polynomials
- external convection from BC `h`
- junction losses as their own grouped heat-loss row
- radiation explicitly absent unless `qr` is present

Remaining caveats are interpretive, not missing ledger columns:

- Junction rows are not bracketed by endpoint enthalpy stations.
- Upcomer enthalpy residuals are diagnostic only because recirculation fractions
  are high.
- Specified-Q rows without layer/h metadata expose imposed duty and wall flux,
  but not a complete external resistance sub-stack.
- Segment residuals are validation diagnostics and must not be fit targets.

## Validation

- `python tools/analyze/build_patchwise_heat_ledger.py`: passed,
  `validation_errors=0`.
- `python -m pytest tools/analyze/test_patchwise_heat_ledger.py`: passed,
  `8 passed`.

## Status

COMPLETE for the requested Heat Sources/Sinks ledger. Downstream model-form work
may consume this as a validation diagnostic, with thermal residuals scored
separately from pressure and mdot.
