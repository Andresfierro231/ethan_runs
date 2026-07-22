# Patchwise Heat Ledger

Generated: `2026-07-08T15:14:26`

## Scope

Formal patchwise heat-source/sink ledger for admitted Salt 2/3/4 Jin mainline
continuations. This is the thermal companion to the July 8 pressure-term ledger.
It is read-only with respect to native solver outputs.

## Contract

- `wallHeatFlux_integral_W` and `heat_to_fluid_W` use the OpenFOAM convention:
  positive is heat into the fluid, negative is heat out of the fluid.
- Rows are grouped by physical role: heater input, cooler removal, passive
  ambient exchange, test-section exchange, and junction/other exchange.
- `heater_imposed_duty_W`, `cooler_removed_duty_W`,
  `passive_wall_heat_leak_gain_W`, and `junction_loss_W` provide the role-level
  heat-source/sink terms requested for closure audits.
- `enthalpy_change_W` is computed from
  `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv` using the Jin salt cp and the mdot already admitted by
  the source heat ledger. Junction rows remain unbracketed.
- `wallHeatFlux_vs_enthalpy_residual_W` is a segment residual:
  segment wallHeatFlux sum minus segment enthalpy-flow change. It is repeated on
  rows in the same segment so each patch group is fit-ready without extra joins.
- The resistance network is resolved from available OpenFOAM outputs as:
  effective internal convection from wall T minus bulk T, BC wall/layer
  conduction from `thicknessLayers` and `kappaLayerCoeffs`, external convection
  from BC `h`, grouped junction losses, and radiation only if a `qr` output
  field exists.
- `radiation_present=False` means no OpenFOAM `qr` output term was found. Surface
  emissivity metadata alone is not treated as a radiation heat ledger term.
- All rows are validation diagnostics, not fit targets.

## Outputs

- `patchwise_heat_ledger.csv`
- `patchwise_heat_ledger.json`
- `summary.json`
- `README.md`

## Counts

- Rows: `24`
- Source ids: `3`
- Patch groups: `{'ambient_wall': 12, 'cooler': 3, 'heater': 3, 'junction_other': 3, 'test_section': 3}`
- Validation errors: `0`

## Aggregate Wall-Flux Sums

```json
{
  "viscosity_screening_salt_test_2_jin_coarse_mesh": {
    "heater_imposed_duty_W": 265.7,
    "heater_input_W": 243.519,
    "heater_imposed_minus_wallHeatFlux_W": 22.181,
    "cooler_imposed_duty_W": -136.351,
    "cooler_removal_W": -136.351,
    "test_section_wallHeatFlux_W": -5.68,
    "net_wallHeatFlux_W": 0.127,
    "net_fraction_of_heater": 0.000519,
    "max_abs_segment_enthalpy_residual_W": 162.437
  },
  "viscosity_screening_salt_test_3_jin_coarse_mesh": {
    "heater_imposed_duty_W": 297.5,
    "heater_input_W": 273.155,
    "heater_imposed_minus_wallHeatFlux_W": 24.345,
    "cooler_imposed_duty_W": -150.77,
    "cooler_removal_W": -150.77,
    "test_section_wallHeatFlux_W": -10.545,
    "net_wallHeatFlux_W": 0.286,
    "net_fraction_of_heater": 0.001048,
    "max_abs_segment_enthalpy_residual_W": 135.569
  },
  "viscosity_screening_salt_test_4_jin_coarse_mesh": {
    "heater_imposed_duty_W": 337.6,
    "heater_input_W": 310.487,
    "heater_imposed_minus_wallHeatFlux_W": 27.113,
    "cooler_imposed_duty_W": -169.227,
    "cooler_removal_W": -169.227,
    "test_section_wallHeatFlux_W": -16.769,
    "net_wallHeatFlux_W": 0.079,
    "net_fraction_of_heater": 0.000255,
    "max_abs_segment_enthalpy_residual_W": 162.689
  }
}
```

## Interpretation Notes

- Cooler specified duty matches `wallHeatFlux` closely for these rows; heater
  specified duty exceeds realized interface `wallHeatFlux`, so heater residuals
  should be interpreted as boundary/solid/storage or staging mismatch until a
  same-time solid-energy audit is available.
- Upcomer rows are diagnostic only because the endpoint-temperature source shows
  high recirculation fractions; treat those residuals as recirculation-cell
  evidence, not pipe-friction closure evidence.
- Specified-Q boundary rows without layer/h metadata still carry imposed duty,
  wall flux, wall temperature, and segment residuals, but their external
  resistance sub-stack is intentionally blank.
