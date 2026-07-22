---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv
  - work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv
  - reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/cfd_sensor_reference.csv
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_case_admission_inventory/cfd_case_admission_inventory.csv
tags: [forward-model, predictive-1d, mdot, sensor-prediction, boundary-conditions]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: AGENT-360
date: 2026-07-14
role: Forward-pred/BC-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# mdot and TP/TW Probe Error Audit

## Purpose

This package audits current 1D model predictivity against Salt1/Salt2/Salt3/Salt4
CFD by comparing mass-flow error with TP/TW temperature-probe error. It is an
assessment package, not a new closure calibration.

## Main Guardrails

- Salt1 is included as diagnostic/context only and is blocked for CFD heat-flux
  modes because the consumed current patch heat ledger covers Salt2/Salt3/Salt4.
- Salt2/Salt3/Salt4 retain the current train/validation/holdout split.
- Any mode consuming realized CFD wallHeatFlux is CFD-informed diagnostic
  evidence, not a setup-only prediction.
- Fixed-mdot rows are thermal isolation diagnostics, not hydraulic predictivity
  evidence.
- CFD rcExternalTemperature radiation is embedded in total wallHeatFlux; no
  separate exported qr term is added.

## Result Counts

- Case rows: `4`.
- Model result rows: `16`.
- Executed model rows: `12`.
- Sensor error rows: `204`.
- Heat score rows: `23`.

## Files To Open

1. `paper_ready_report.md`
2. `mdot_error_summary.csv`
3. `temperature_probe_error_summary.csv`
4. `sensor_level_errors.csv`
5. `part3_test_section_error_increment.csv`
6. `part4_cooling_rmse_summary.csv`
7. `part5_heating_rmse_summary.csv`
8. `mdot_temperature_error_correlation.csv`
9. `trend_conclusion_register.csv`
10. `model_config_appendix/appendix_explanation.md`
