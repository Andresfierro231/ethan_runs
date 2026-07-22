# Thermal Boundary Patch-Role Table

Generated: `2026-07-13T10:54:45`
Task: `AGENT-263`

## Scope

Patch-level CFD thermal boundary table for admitted Salt 2/3/4 Jin mainline
continuations. The package reads OpenFOAM `0/T` dictionaries and existing
`wallHeatFlux.dat` postProcessing outputs only. Native solver outputs are not
modified.

## Outputs

- `thermal_boundary_patch_role_table.csv`
- `thermal_boundary_patch_role_table.json`
- `patch_role_area_heat_summary.csv`
- `segment_reduction_inputs.csv`
- `validation_report.json`
- `summary.json`

## Contract

Positive `realized_wallHeatFlux_W` means heat enters the fluid; negative means
heat leaves the fluid. Patch rows preserve imposed `Q`, realized wall flux,
boundary `h`, `Ta`, `Tsur`, emissivity, and wall/layer metadata separately.

Rows with `zero_gradient_ncc_connector` are connector/support patches and are
not 1D fit targets. Junction rows are grouped diagnostics. Segment reduction
rows provide area-weighted external inputs for a future 1D parity mode, not a
new 1D run.

## Counts

- Patch rows: `207`
- Sources: `['viscosity_screening_salt_test_2_jin_coarse_mesh', 'viscosity_screening_salt_test_3_jin_coarse_mesh', 'viscosity_screening_salt_test_4_jin_coarse_mesh']`
- Roles: `{'ambient_wall': 63, 'cooler': 9, 'heater': 9, 'junction_other': 87, 'test_section': 3, 'zero_gradient_ncc_connector': 36}`
- Validation errors: `0`
