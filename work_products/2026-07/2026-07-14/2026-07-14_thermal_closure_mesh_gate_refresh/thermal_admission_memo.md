# Thermal Admission Memo

Task: `AGENT-309`

Generated: `2026-07-14T11:12:22-05:00`

## Decision

No lower-leg, upcomer, or downcomer thermal UA/HTC/Nu row is fit-admissible.
Finite repaired values are validation-only diagnostics unless the table marks
the QOI blocked. The admission table is `thermal_admission_table.csv`.

## Segment Rollup

- `lower_leg`: fit `0`, validation-only `5`, blocked `1`.
- `upcomer`: fit `0`, validation-only `6`, blocked `0`.
- `downcomer`: fit `0`, validation-only `0`, blocked `4`.

Admission counts:

```json
{
  "blocked": 5,
  "validation_only": 11
}
```

## Sign Convention

- Positive `wallHeatFlux` / segment duty means heat enters the fluid.
- Positive `enthalpy_change_W` means bulk fluid enthalpy increases between the
  declared physical segment interfaces.
- `HTC`, `UA_prime`, and `Nu` are positive effective internal-transfer
  diagnostics, not heat-source directions.

## Radiation Semantics

Current CFD `rcExternalTemperature` includes radiation through emissivity and
`Tsur`, and current outputs do not export a separate `qr` term. Treat
`wallHeatFlux` as the total boundary heat flux. Do not add a separate radiation
term on top of CFD `wallHeatFlux`, and do not hide radiation or external-loss
residuals inside internal `Nu`.

## Guardrail

Internal `Nu` must not absorb heater, cooler, passive ambient loss, junction,
wall storage, or radiation residuals. The next admissible step is a heat-balance
and sign-policy review, not thermal fitting.
