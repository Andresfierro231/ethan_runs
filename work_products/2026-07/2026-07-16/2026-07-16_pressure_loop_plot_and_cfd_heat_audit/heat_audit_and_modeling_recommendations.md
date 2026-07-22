# Pressure Loop Plot and CFD Heat Audit

## Pressure Plots

The pressure plots are SVGs generated directly from AGENT-457 station maps. They are diagnostic pressure maps, not admitted hydraulic coefficients.

- `mainline_static_pressure`: `work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/pressure_loop_mainline_static_p.svg`
- `mainline_p_rgh`: `work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/pressure_loop_mainline_p_rgh.svg`
- `all_cases_static_pressure`: `work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/pressure_loop_all_cases_static_p.svg`

## Pressure Map Sanity Check

The x-axis is the AGENT-457 `loop_order_index`, which already applies the label-locked physical flow order. The branch bands map to 1D model regions as follows: lower_leg heater -> `heated_incline`, left lower upcomer -> `left_lower_vertical`, test section -> `test_section`, left upper upcomer -> `left_upper_vertical`, upper cooled leg -> cooled upper run, and right downcomer -> right vertical return. The plotted values preserve the source station labels and the source caveat that every row remains `diagnostic_station_pressure_ladder_not_fit_admitted` until orientation, straight-loss subtraction, and recirculation-mask gates are completed.

The plotted mainline Salt2-4 static-pressure traces nearly overlay one another in shape, which is consistent with the same geometry and station extraction. Static `p` and `p_rgh` are both plotted because AGENT-460 found static-vs-`p_rgh` sign differences at several local deltas. For model fitting, these plots should be read as location/context diagnostics rather than a pressure-drop coefficient source.

## Heat Audit Coverage

Comparable realized CFD heat accounting was found for `4` pressure-map cases. Missing comparable heat ledgers: `salt1_hi10q;salt1_lo10q;salt1_nominal;salt2_hi5q;salt2_lo5q;salt4_hi5q;salt4_lo5q`.

| case | heater to fluid W | cooler W | junction/stub W | passive loss excl cooler W | junction/passive | notes |
|---|---:|---:|---:|---:|---:|---|
| `salt2_mainline` | 243.519 | -136.351 | -39.128 | 107.042 | 0.366 | role_level_cfd_heat_accounting |
| `salt3_mainline` | 273.155 | -150.770 | -43.235 | 122.099 | 0.354 | role_level_cfd_heat_accounting |
| `salt4_mainline` | 310.487 | -169.227 | -48.485 | 141.181 | 0.343 | role_level_cfd_heat_accounting |
| `val_salt2` | 244.631 | -136.351 | -40.926 | 108.087 | 0.379 | section_level_cfd_heat_ledger |

## Heat Balance Critique

The Salt2-4 role-level audits are physically coherent in aggregate: heater-to-fluid heat is positive, cooler and passive surfaces are negative, and the realized wall-flux sums close within about 0.3 W. The val_salt2 section ledger also closes tightly, with a reported total of about 0.19 W. That closure supports using these rows for a heat-loss audit, but not for local junction calibration because the junction/stub values are aggregated patch groups.

The missing heat-ledger cases are not failed cases; they are pressure-mapped cases without a comparable realized heat accounting artifact in the current work products. They should stay absent from heat-loss trends until a matching heat ledger is harvested with the same sign convention and role definitions.

## Per-Run Heat Audit

- `salt2_mainline`: heater to fluid 243.519 W (265.7 W imposed); cooler -136.351 W; test section -5.680 W; junction/stub -39.128 W. Junction/stub loss is 36.6% of passive non-cooler loss and 14.7% of imposed heater power.
- `salt3_mainline`: heater to fluid 273.155 W (297.5 W imposed); cooler -150.770 W; test section -10.545 W; junction/stub -43.235 W. Junction/stub loss is 35.4% of passive non-cooler loss and 14.5% of imposed heater power.
- `salt4_mainline`: heater to fluid 310.487 W (337.6 W imposed); cooler -169.227 W; test section -16.769 W; junction/stub -48.485 W. Junction/stub loss is 34.3% of passive non-cooler loss and 14.4% of imposed heater power.
- `val_salt2`: heater to fluid 244.631 W (not recorded in source); cooler -136.351 W; test section -7.458 W; junction/stub -40.926 W. Junction/stub loss is 37.9% of passive non-cooler loss and not available.

## Junction/Stub Heat-Loss Interpretation

The CFD shows junction/stub heat loss is not a small numerical artifact. In Salt2-4 mainline it rises from about 39 W to 48 W as operating power/temperature rises, while remaining roughly 14-15% of imposed heater power and about one third of non-cooler passive losses.

The large value is physically plausible because the junction/stub group is an aggregate of many exposed connector patches, not a single bend. In the Salt2-4 role table it contains 29 patches with about 0.04248 m2 of area; the same row mixes 11 `rcExternalTemperature`, 7 `externalTemperature`, and 11 `zeroGradient` patches. Those surfaces have concentrated area near hot junctions, 3D conduction paths through fittings/stubs, and external boundary conditions that include radiation in total `wallHeatFlux`. That combination makes per-area heat loss high compared with long insulated pipe surfaces.

Scientifically, this means the current 1D model should not hide junction/stub loss in a global insulation fudge factor. It should carry explicit localized loss terms or surface groups.

## Ways The 1D Model Could Improve Junction Heat-Loss Treatment

1. Add explicit zero-length junction/stub thermal nodes at lower-left, lower-right, upper-right, and upper-left.
2. Give each junction node its own external area, effective wall/insulation resistance, ambient temperature, emissivity, and convection coefficient.
3. Split `junction_other` into the four physical junctions in future CFD postprocessing so the 1D model can fit/validate local losses instead of one aggregate term.
4. Treat radiation as inseparable from realized CFD `wallHeatFlux` unless future extraction preserves radiative and convective pieces separately.
5. Couple the thermal loss to local fluid temperature, not a global loop mean, because junctions sit at very different temperatures.
6. Preserve setup-only predictive legality: fit parameters may come from training, but runtime prediction must not consume realized CFD `wallHeatFlux`.

## Trend Notes

- junction_loss_vs_power: Salt2-4 junction/stub heat loss increases monotonically 39.128 -> 48.485 W as imposed heater power increases 265.7 -> 337.6 W.
- junction_fraction_of_heater: Junction loss fraction of imposed heater is nearly flat: 0.147, 0.145, 0.144. This suggests a structurally persistent local heat path rather than a one-case anomaly.
- junction_flux: Junction/stub heat flux magnitude rises 921.1 -> 1141.4 W/m2 over Salt2-4, consistent with higher local temperatures driving external losses.

## Junction Heat Loss And Corner Pressure Drop State

We understand the junction heat loss at the role/section level, not at individual physical junction resolution. The strongest present conclusion is that the aggregate junction/stub thermal pathway is persistent and scales with operating temperature/power. We do not yet have enough split-by-junction evidence to assign loss to lower-left versus lower-right versus upper-right versus upper-left in the 1D model.

We do not yet have an admitted corner pressure-drop model. AGENT-460 found corner-pressure diagnostics, but they remain upper-bound/local diagnostics because the pressure rows are still blocked by orientation, straight-loss subtraction, and recirculation-mask admission. They are useful for prioritizing where to extract better evidence, not for final K-factor fitting.

## Provenance

- Pressure station source: `work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/all_streamwise_pressure_1d_map.csv`
- Pressure scientific review: `work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/scientific_review.md`
- Salt2-4 heat source: `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv`
- val_salt2 heat source: `work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/val_salt2_section_heat_loss_ledger.csv`
- Reusable builder: `tools/analyze/build_pressure_loop_plot_and_cfd_heat_audit.py`
- Tests: `tools/analyze/test_pressure_loop_plot_and_cfd_heat_audit.py`
