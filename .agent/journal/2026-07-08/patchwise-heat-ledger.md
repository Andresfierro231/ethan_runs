# Patchwise Heat Ledger

Date: `2026-07-08`
Task: `TODO-PATCHWISE-HEAT-LEDGER`
Role: Implementer / Tester / Writer
Owner: codex

## Context Read

Claimed after completing `TODO-OBSERVATION-TABLE-CONTRACT` and
`TODO-PRESSURE-TERM-LEDGER`. Additional mechanistic heat-ledger context read:

- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `.agent/status/2026-07-07_AGENT-194.md`
- `work_products/2026-07-07_heat_source_sink_ledger/README.md`
- `work_products/2026-07-07_heat_source_sink_ledger/summary.json`
- `work_products/2026-07-08_span_endpoint_temperatures/README.md`
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`

## Work Completed

Extended the July 8 patchwise heat ledger into the requested Heat
Sources/Sinks ledger:

- `tools/analyze/build_patchwise_heat_ledger.py`
- `tools/analyze/test_patchwise_heat_ledger.py`

Regenerated:

- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.json`
- `work_products/2026-07-08_patchwise_heat_ledger/summary.json`
- `work_products/2026-07-08_patchwise_heat_ledger/README.md`

The ledger now includes heater imposed duty, cooler removed duty, passive wall
heat leak/gain, junction losses, segment enthalpy-flow change, wallHeatFlux
integral, segment residual, BC type, sign convention, patch area, reconstructed
wall temperature, effective internal convection, wall/layer conduction,
external convection, and explicit radiation availability.

## Observed Facts

- `24` rows across Salt 2/3/4 Jin.
- Cooler imposed duty matches wallHeatFlux to within `0.001 W` for all three
  cases.
- Heater imposed duty exceeds realized wallHeatFlux:
  - Salt 2: `265.7 W` imposed vs `243.519 W` wallHeatFlux.
  - Salt 3: `297.5 W` imposed vs `273.155 W` wallHeatFlux.
  - Salt 4: `337.6 W` imposed vs `310.487 W` wallHeatFlux.
- Test-section imposed duty is `37 W`, but the wallHeatFlux row is a net sink:
  - Salt 2: `-5.68 W`
  - Salt 3: `-10.545 W`
  - Salt 4: `-16.769 W`
- Segment enthalpy residuals are now populated for lower leg, cooling branch,
  downcomer, and upcomer rows using
  `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`.
- Junction rows intentionally have no enthalpy residual because the endpoint
  temperature artifact does not bracket junction volumes.
- No OpenFOAM `qr` output term was found. Radiation is therefore absent from the
  extracted heat ledger even though emissivity metadata exists in `0/T`.

## Inferred Interpretation

The Salt heat-loss separation is no longer only case-level/audit-style. It is a
patch-group/segment ledger with the complete available resistance network:

- wallHeatFlux interface heat into/out of the fluid
- effective internal convection from wall T minus bulk T
- BC wall/layer conduction from thickness/kappa metadata
- external convection from BC `h`
- junction losses grouped separately
- radiation only if `qr` is exposed

The strongest thermal contradictions remain scientific interpretation issues:
heater imposed duty is not fully realized as interface wallHeatFlux, and the
test section is locally a sink despite imposed heat. Upcomer residuals should be
treated as recirculation-cell diagnostics, not pipe-friction closure evidence.

## Blockers

No implementation blocker remains for the requested ledger. Remaining caveats:

- Junction enthalpy closure needs dedicated junction-bracketing surfaces.
- Specified-Q rows without layer/h metadata cannot expose a full external
  resistance sub-stack.
- Radiation cannot be quantified unless a `qr` output term is written by the
  OpenFOAM case.

## Validation

- `python tools/analyze/build_patchwise_heat_ledger.py`: passed with
  `validation_errors=0`.
- `python -m pytest tools/analyze/test_patchwise_heat_ledger.py`: passed,
  `8 passed`.

## Recommended Next Action

`TODO-MODEL-FORM-BAKEOFF` may consume this ledger as the common thermal
validation table. Score pressure distribution, mdot, and thermal-state mismatch
separately, and keep upcomer/junction heat residuals out of fit targets.
