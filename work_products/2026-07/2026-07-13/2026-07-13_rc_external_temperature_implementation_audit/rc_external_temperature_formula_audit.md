# rcExternalTemperature Implementation Audit

Generated: `2026-07-13T10:54:46`
Task: `AGENT-264`

## Result

- `emissivity_Tsur_affect_heat_flux`: `yes`
- `parity_radiation_mode`: `inseparable`
- `separable_radiation_output_available`: `no`

The accessible custom C++ source was not found in targeted locations, so this
audit does not quote an exact custom-source formula. The compiled
`libRCWallBC.so` is readable and exposes `rcExternalTemperature`, `updateCoeffs`,
`emissivity`, `Tsur`, OpenFOAM `physicoChemical::sigma`, and radial/resistance
symbols including `Rps`, `RpsInner`, `RpsOuter`, `CpAreal`, and `CsAreal`.

Interpretation: emissivity/Tsur are active in the custom boundary heat-flux
calculation, but the current CFD outputs do not expose a separate radiation
heat-rate ledger. Radiation is therefore inseparable from total
`wallHeatFlux` for current parity work.

## 1D Parity Instruction

For realized-wallHeatFlux diagnostic replay, do not add a separate 1D radiation term on top of CFD wallHeatFlux. For external-BC parity mode, treat radiation as inseparable inside the rcExternalTemperature equivalent unless a future OpenFOAM output or source audit exposes a separate qr/radiation heat term.

## Evidence

- `custom_source_probe`: Custom source is not available in the targeted accessible locations; use compiled-library and dictionary evidence.
- `compiled_library_strings`: The compiled BC stores rcExternalTemperature, emissivity, Tsur, layer metadata, and constructor diagnostics requiring Ta or Tsur with emissivity.
- `compiled_library_symbols`: The compiled BC defines updateCoeffs and radiation/resistance-related methods and references OpenFOAM sigma.
- `stock_externalTemperature_reference`: Stock OF13 externalTemperature combines emissivity with sigma into an effective heat-transfer coefficient and only exports separate radiation when a qr field is configured; this is an analogy, not the custom source.
- `admitted_case_dictionary_fields`: All admitted Salt 2/3/4 rcExternalTemperature patches carry emissivity and Tsur metadata in the AGENT-263 table.
- `no_exported_radiation_ledger`: Radiation is not separable from total OpenFOAM wallHeatFlux in the available outputs.

## Validation Errors

```json
[]
```
