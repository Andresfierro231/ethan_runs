# TODO-LITREV-HEAT-LOSS-CALIBRATION Status

Date: `2026-07-13`

Role: `Implementer / Tester / Writer`

## Observed Facts

- Built `work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/`.
- Primary outputs:
  - `separated_heat_loss_ledger.csv`: 207 heat-path rows.
  - `heat_closure_admission.csv`: 18 segment admission rows.
- Cooler/jacket, passive convection, rcExternalTemperature radiation metadata,
  heater input, wall/storage unknowns, and residual are kept separate.

## Inferred Interpretation

Internal HTC/Nu must not absorb external heat-loss residuals. Radiation is
bounded as inseparable metadata inside realized `wallHeatFlux` unless a future
package exposes an independent `qr` term.

## Blockers

No separate radiation heat term is observed in the current package. Wall/storage
is not independently measured and remains residual/assumption status.

## Files Used

- `tools/analyze/build_litrev_heat_loss_calibration.py`
- `tools/analyze/test_litrev_heat_loss_calibration.py`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/control_volume_effective_thermal_table.csv`

## Validation

- `python3.11 tools/analyze/test_litrev_heat_loss_calibration.py`
- `python3.11 tools/analyze/build_litrev_heat_loss_calibration.py`

## Recommended Next Action

Use `heat_closure_admission.csv` as the guardrail before any internal Nu/UA
calibration. Add a radiation-specific task only if an independent radiation term
or surface-radiation estimate is available.

