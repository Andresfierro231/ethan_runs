# TODO-LITREV-PROPERTY-SENSITIVITY Status

Date: `2026-07-13`

Role: `Implementer / Tester / Writer`

## Observed Facts

- Built `work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/`.
- Primary outputs:
  - `property_mode_matrix.csv`: 90 branch/property rows.
  - `property_sensitivity_summary.csv`: 15 case/property-mode summary rows.
- The package compares replication Reis/Jadyn, Sohal/Janz, Jin+Parida+Santini,
  Jin+1560+0.60, and Shen Celsius-basis comparison modes.

## Inferred Interpretation

Property choices materially move `Re`, `Pr`, and `Gz`; closure fitting should
not proceed until replication and updated-property lanes are explicitly chosen.

## Blockers

This is a first-order postprocessing sensitivity. It does not rerun Fluid or
solve a new pressure-rooted 1D model.

## Files Used

- `tools/analyze/build_litrev_property_sensitivity.py`
- `tools/analyze/test_litrev_property_sensitivity.py`
- `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/control_volume_effective_thermal_table.csv`

## Validation

- `python3.11 tools/analyze/test_litrev_property_sensitivity.py`
- `python3.11 tools/analyze/build_litrev_property_sensitivity.py`

## Recommended Next Action

Run any full 1D property-mode sensitivity as a follow-up only after choosing
which rows are replication, calibration, and validation lanes.

