# Setup, Boundary-Condition, Model-Form, and Error Synthesis

Generated: 2026-07-15

## Executive Answer

The clearest current result is that matching where heat is placed with
CFD-realized values is useful diagnostically, but it is not yet a predictive
model. The pressure-root diagnostic ladder gives these averaged Salt2/Salt3/Salt4
errors:

- M1 full CFD segment heat ledger: mdot mean absolute error
  35.874 pct and all-probe RMSE
  159.168 K.
- M2 CFD heater + test-section net + cooler: mdot mean absolute error
  10.397 pct and all-probe RMSE
  26.972 K.
- M3 CFD heater + cooler only: mdot mean absolute error
  16.826 pct and all-probe RMSE
  18.023 K.

M2 is the best current combined mdot/temperature diagnostic mode. M3 has lower
temperature-probe RMSE, but a worse mdot error, which means the test-section
term is changing buoyancy and hydraulic state rather than being negligible.
M1 is the strongest warning: even full realized segment heat placement leaves a
large thermal-state error in the current 1D state representation.

The exact section-placement replay exists as diagnostic-only evidence; it forces CFD-realized wallHeatFlux locations and therefore admits zero predictive rows. Its maximum forced residual is 0 W.

## Case Setup

| case | split | fit? | CFD mdot kg/s | CFD Tmean K | CFD loop dT K | heater W | test-section W | Ta K | patch heat ledger |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| salt_1 | diagnostic-only | no | 0.01123 | 428.72 |  | 232.3 | 37 | 299.11 | no |
| salt_2 | train | yes | 0.01318 | 450.3 | 12.1 | 265.7 | 37 | 299.19 | yes |
| salt_3 | validation | no | 0.01497 | 463.7 | 12.2 | 297.5 | 37 | 299.79 | yes |
| salt_4 | holdout | no | 0.01698 | 479.2 | 12.3 | 337.6 | 37 | 299.97 | yes |

Salt2 is the declared training row, Salt3 is validation, and Salt4 is holdout.
Salt1 is context only in this audit because the consumed source set lacks a
current admitted Salt1 patch heat ledger.

## Boundary Conditions And Model Forms

| mode | description | solver policy | class | uses CFD mdot | uses realized wallHeatFlux | model/closure terms |
| --- | --- | --- | --- | --- | --- | --- |
| M1_full_cfd_segment_heat_flux_pressure_root | Prescribe full CFD realized segment heat ledger and solve mdot from pressure balance. | pressure_root_fast_scan | diagnostic_cfd_informed_upper_bound | no | yes | Fluid geometry; default MinorLosses; default friction closure; prescribed CFD heat sources/losses. |
| M1b_full_cfd_segment_heat_flux_fixed_mdot | Same full CFD heat ledger, but CFD mdot is imposed to isolate thermal/sensor error. | fixed_cfd_mdot_pressure_residual_diagnostic | diagnostic_fixed_mdot_thermal_isolation | yes | yes | Fluid thermal periodicity; default MinorLosses pressure residual only; full prescribed CFD heat losses. |
| M2_cfd_heater_test_section_cooler_pressure_root | Prescribe CFD heater, test-section net sink, and cooler heat removal; solve mdot. | pressure_root_fast_scan | diagnostic_cfd_informed_boundary_subset | no | yes | Imposed qhx for cooler; negative test-section source to preserve current passive model; default friction/minor losses. |
| M3_cfd_heater_cooler_pressure_root | Prescribe CFD heater and cooler heat removal only; solve mdot. | pressure_root_fast_scan | diagnostic_cfd_informed_boundary_subset | no | yes | Imposed qhx for cooler; no CFD test-section term; default friction/minor losses. |

Interpretation:

- M1 and M1b consume the realized CFD heat ledger and are diagnostic upper-bound
  or isolation studies, not setup-only predictions.
- M2 and M3 solve mdot from pressure balance, but still consume CFD-realized
  heater/cooler/test-section thermal terms. They are diagnostic boundary-form
  comparisons.
- Fixed-mdot rows isolate thermal behavior only and should not be presented as
  hydraulic predictions.

## Resulting Errors

| mode | mean abs mdot % | mean abs mdot kg/s | mean all-probe RMSE K | class |
| --- | --- | --- | --- | --- |
| M1_full_cfd_segment_heat_flux_pressure_root | 35.874 | 0.00547 | 159.168 | diagnostic_cfd_informed_upper_bound |
| M1b_full_cfd_segment_heat_flux_fixed_mdot |  |  | 152.212 | diagnostic_fixed_mdot_thermal_isolation |
| M2_cfd_heater_test_section_cooler_pressure_root | 10.397 | 0.00157 | 26.972 | diagnostic_cfd_informed_boundary_subset |
| M3_cfd_heater_cooler_pressure_root | 16.826 | 0.00256 | 18.023 | diagnostic_cfd_informed_boundary_subset |

### Per-Case Error Matrix

| case | split | mode | 1D mdot kg/s | CFD mdot kg/s | mdot error % | all-probe RMSE K | TP RMSE K | TW RMSE K | Tmean error K | loop dT error K |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| salt_2 | train | M1_full_cfd_segment_heat_flux_pressure_root | 0.01953 | 0.01318 | 48.189 | 75.853 | 74.246 | 76.645 | -77.018 | -3.589 |
| salt_2 | train | M2_cfd_heater_test_section_cooler_pressure_root | 0.01453 | 0.01318 | 10.252 | 24.331 | 20.998 | 25.837 | -23.908 | -1.557 |
| salt_2 | train | M3_cfd_heater_cooler_pressure_root | 0.01516 | 0.01318 | 14.994 | 19.349 | 15.649 | 20.955 | -18.341 | -2.058 |
| salt_3 | validation | M1_full_cfd_segment_heat_flux_pressure_root | 0.01484 | 0.01497 | -0.843 | 192.201 | 190.75 | 192.922 | -194.903 | 0.369 |
| salt_3 | validation | M2_cfd_heater_test_section_cooler_pressure_root | 0.01641 | 0.01497 | 9.594 | 26.484 | 23.597 | 27.815 | -26.793 | -1.707 |
| salt_3 | validation | M3_cfd_heater_cooler_pressure_root | 0.01734 | 0.01497 | 15.857 | 17.749 | 14.06 | 19.332 | -16.92 | -2.381 |
| salt_4 | holdout | M1_full_cfd_segment_heat_flux_pressure_root | 0.00703 | 0.01698 | -58.591 | 209.45 | 204.433 | 211.914 | -212.777 | 17.877 |
| salt_4 | holdout | M2_cfd_heater_test_section_cooler_pressure_root | 0.01891 | 0.01698 | 11.344 | 30.102 | 27.536 | 31.306 | -30.403 | -1.927 |
| salt_4 | holdout | M3_cfd_heater_cooler_pressure_root | 0.02031 | 0.01698 | 19.626 | 16.971 | 13.056 | 18.623 | -15.51 | -2.792 |

## Heater And Cooler Model-Form Error

| leg | model form | scope | RMSE W | MAE W | mean error W | fit policy |
| --- | --- | --- | --- | --- | --- | --- |
| cooling_leg | current_fluid_airside_hx_fixed_mdot | all_non_salt1 | 102.886 | 102.35 | -102.35 | setup_model_or_current_fluid_diagnostic |
| cooling_leg | imposed_cfd_cooler_upper_bound | all_non_salt1 | 0 | 0 | 0 | diagnostic_upper_bound_not_predictive |
| cooling_leg | salt2_fit_constant_UA_bulk_drive | all_non_salt1 | 4.638 | 3.457 | -3.457 | fit_on_salt2_score_salt3_salt4_salt1_excluded |
| cooling_leg | salt2_fit_cooler_imposed_ratio | all_non_salt1 | 8.018e-07 | 4.972e-07 | 4.972e-07 | fit_on_salt2_score_salt3_salt4_salt1_excluded |
| heating_leg | electrical_heater_power_1_to_1 | all_non_salt1 | 24.629 | 24.546 | 24.546 | setup_model_diagnostic |
| heating_leg | imposed_cfd_heater_upper_bound | all_non_salt1 | 0 | 0 | 0 | diagnostic_upper_bound_not_predictive |
| heating_leg | salt2_fit_constant_heater_efficiency | all_non_salt1 | 0.68 | 0.52 | -0.52 | fit_on_salt2_score_salt3_salt4_salt1_excluded |

The cooler model is the strongest immediate boundary-model lever. The current
fixed-mdot airside-HX representation under-removes heat by about 102 W MAE over
Salt2/Salt3/Salt4, while a Salt2-fit constant-UA bulk-drive diagnostic reduces
the all-non-Salt1 RMSE to about 4.64 W. The heater mismatch is smaller but still
important: electrical 1:1 heater power has about 24.63 W RMSE, while a Salt2-fit
heater-efficiency diagnostic transfers to Salt3/Salt4 with about 0.68 W RMSE.

## Setup-Predictive Variant Status

The implemented setup-predictive variant now has the Fluid hooks needed to
replace realized CFD heat-loss replay with setup-only inputs:

| field | status | accepted values | purpose | leakage guardrail |
| --- | --- | --- | --- | --- |
| outer_closure_mode | implemented | baseline; per_parent_multiplier; external_boundary_table | activates setup-only per-segment external-boundary loss calculation | none_by_itself |
| external_boundary_h_by_parent_segment | implemented | mapping parent_or_segment -> W/m2/K | prescribed setup external h instead of natural-convection correlation on targeted rows | must come from setup/boundary dictionary, not realized wallHeatFlux |
| external_boundary_ambient_temperature_by_parent_segment | implemented | mapping parent_or_segment -> K | per-segment ambient Ta drive | setup_only |
| external_boundary_surroundings_temperature_by_parent_segment | implemented | mapping parent_or_segment -> K | per-segment Tsur metadata for radiation-enabled setup calculations | setup_only |
| external_boundary_emissivity_by_parent_segment | implemented | mapping parent_or_segment -> emissivity | per-segment setup emissivity metadata | setup_only |
| external_boundary_coverage_multiplier_by_parent_segment | implemented | positive mapping parent_or_segment -> multiplier | junction/stub/connector heat-loss area coverage without CFD wallHeatFlux | setup geometry only; do not fit to held-out realized heat loss |
| external_boundary_drive_selector_by_parent_segment | implemented | fluid_segment_bulk_temperature_for_v1_setup_mode; pipe_outer_wall_temperature; outer_surface_temperature | choose bulk, wall/shell, or outer-surface effective driving temperature | uses solver-state temperatures only |
| hx_ua_multiplier | compatible_existing_hook | nonnegative scalar | setup-only HX/cooler UA scaling; separate from passive external-boundary loss | not imposed cooler duty |

This is an implementation unlock, not a final admitted predictive score. It
still needs a declared split, fit on training rows only, and validation/holdout
scoring without realized CFD wallHeatFlux, CFD mdot, imposed CFD cooler duty, or
validation temperatures at runtime.

## Assumptions And Guardrails

| ID | topic | assumption | risk if violated |
| --- | --- | --- | --- |
| A001 | wallHeatFlux sign | Positive CFD wallHeatFlux means heat enters the fluid; negative means heat leaves the fluid. | Wrong sign reverses heater/cooler/test-section interpretation. |
| A002 | radiation | CFD rcExternalTemperature includes radiation in total wallHeatFlux; current CFD exports no separate qr. | Do not double count radiation as a separate 1D term when prescribing CFD heat flux. |
| A003 | runtime discipline | Realized CFD wallHeatFlux is diagnostic evidence unless a mode explicitly declares itself CFD-informed. | CFD-informed modes are not final setup-only predictions. |
| A004 | fixed mdot | Fixed-mdot modes impose CFD mdot and therefore isolate thermal/sensor behavior only. | Do not use fixed-mdot rows as hydraulic predictivity evidence. |
| A005 | test-section sink encoding | For M2, CFD test-section net loss is encoded as a negative source to preserve current Fluid passive boundary behavior. | This is a compatibility representation, not a first-class external boundary model. |
| A006 | sensor targets | TP targets use CFD core/bulk probe references; TW targets use CFD wall-area-average probe references. | Sensor-coordinate uncertainty remains a score limitation. |
| A007 | split discipline | Salt2 is the current train row, Salt3 validation, Salt4 holdout, and Salt1 diagnostic/context only. | No model form is fit on validation or holdout rows. |
| A008 | Salt1 | Salt1 has sensor and Fluid setup references but lacks a current admitted Salt1 patch heat ledger in the consumed source set. | Salt1 is reported as diagnostic and blocked for CFD heat-flux modes. |
| A009 | closures | Fluid default geometry, default MinorLosses, default friction closure, 1.0 inch insulation, and current solver thermal model are used unless the mode says otherwise. | This is an audit of the current 1D model, not a new closure calibration. |

## Presentation-Ready Takeaways

1. The current best combined diagnostic boundary mode is M2, not because it is
   predictive, but because it balances mdot and temperature errors better than
   the other realized-CFD boundary modes.
2. M3 has the best temperature-probe RMSE, but worsens mdot. That tradeoff is
   the evidence that heat placement changes buoyancy and flow, not just sensor
   offsets.
3. Full CFD heat-ledger replay does not solve the 1D state error by itself.
   The model still needs better reference-temperature, wall/shell-drive, and
   thermal-development treatment.
4. Cooler/HX closure is the largest near-term setup-only model improvement.
5. Heater closure is tractable as a scalar efficiency or thermal-resistance
   model, but it must be setup-only before predictive admission.

## Source Paths

- `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit`
- `work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation`
- `work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger`
- `work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant`
- `work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan`
