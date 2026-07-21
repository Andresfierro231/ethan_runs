# AGENT-263 Thermal Boundary Patch-Role Table

Timestamp: 2026-07-13T10:55:00-0500
Role: Coordinator / Implementer / Tester / Writer

## Observed Output

Built `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/`.

Primary files:

- `thermal_boundary_patch_role_table.csv`
- `patch_role_area_heat_summary.csv`
- `segment_reduction_inputs.csv`
- `validation_report.json`
- `summary.json`
- `README.md`

The patch table contains 207 rows across admitted Salt 2/3/4 Jin mainline
continuations. Per-source `0/T` counts remain 69 patches with
`externalTemperature:10`, `rcExternalTemperature:36`, and `zeroGradient:23`.

Patch-level sums match the July 8 grouped patchwise heat ledger within the
declared tolerance. The generated validation report has zero errors.

## Interpretation

The table preserves the boundary contract at patch grain: patch name, role, BC
type, area, `h`, `Ta`, `Tsur`, emissivity, wall/layer metadata, imposed heat,
realized `wallHeatFlux`, and 1D segment mapping. This is the clean source for a
future external-BC parity reduction.

The segment reduction rows are diagnostic inputs, not a 1D run. Junction rows
remain grouped diagnostics, and zero-gradient NCC connector rows are not fit
targets.

## Commands

```bash
python tools/analyze/build_thermal_boundary_patch_role_table.py
pytest -q tools/analyze/test_thermal_boundary_patch_role_table.py tools/analyze/test_rc_external_temperature_implementation_audit.py
```

## Boundaries

No native solver outputs, staged case dictionaries, scheduler state, or external
Fluid files were modified.
