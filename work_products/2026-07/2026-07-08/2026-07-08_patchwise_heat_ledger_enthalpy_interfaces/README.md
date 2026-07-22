# Patchwise Heat Ledger With Physical Interface Enthalpy

Generated: `2026-07-08T17:18:41`

## Scope

Follow-up package for `TODO-HEAT-ENTHALPY-INTERFACE-LEDGER`. This package keeps
`work_products/2026-07-08_patchwise_heat_ledger/` read-only and writes a new enthalpy/residual layer based
on explicit physical segment interfaces sampled from existing `secmeanSurfaces`
XY planes.

## Contract

- Positive `wallHeatFlux_integral_W` and `heat_to_fluid_W` mean heat enters the
  fluid; negative values mean heat leaves the fluid.
- `enthalpy_change_W = mdot * cp * (T_out - T_in)` with Jin salt
  `cp = 1423.47 J/kg/K`.
- Interface temperatures use mixing-cup bulk temperature unless recirculation
  ratio exceeds `0.5`; high-recirculation interfaces use forward-flow bulk
  temperature and are diagnostic only.
- Junction rows remain unbracketed because no single inlet/outlet interface pair
  encloses the grouped junction patches.
- Radiation is a heat-ledger term only when OpenFOAM exposes `qr`. These rows
  retain the July 8 no-`qr` status and do not infer radiation from emissivity
  metadata alone.

## Outputs

- `interface_registry.csv`
- `interface_temperature_samples.csv`
- `segment_enthalpy_residuals.csv`
- `patchwise_heat_ledger_enthalpy_interfaces.csv`
- `patchwise_heat_ledger_enthalpy_interfaces.json`
- `resistance_network_terms.csv`
- `source_inventory.csv`
- `summary.json`
- `README.md`

## Counts

- Patchwise rows: `24`
- Segment residual rows: `15`
- Validation errors: `0`
- Segment statuses: `{'computed_from_physical_interfaces_partial_cooler_bracket': 3, 'computed_from_physical_interfaces_high_recirculation_flag': 3, 'not_bracketed_by_physical_segment_interfaces': 3, 'computed_from_physical_segment_interfaces': 3, 'computed_diagnostic_only_high_recirculation_interfaces': 3}`
- Max absolute segment residual: `162.689 W`

## Interpretation

This package improves the July 8 foundation by making the control-volume
interfaces explicit. It does not magically make every heat row fit-ready:
cooler rows are still only partially bracketed by available upper-leg cut
planes, upcomer rows remain recirculation-cell diagnostics, and junction rows
remain wall-flux-only until dedicated junction-bracketing surfaces exist.

## Validation Errors

```json
[]
```
