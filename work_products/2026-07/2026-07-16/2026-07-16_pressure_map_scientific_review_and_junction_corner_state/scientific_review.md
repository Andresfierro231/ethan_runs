# Pressure Map Scientific Review and Junction/Corner State

## Bottom Line

The AGENT-457 pressure-map outputs make sense as complete, provenance-rich station and branch pressure maps. They do not make sense as admitted hydraulic closure evidence. Every branch remains diagnostic because the current harvest still lacks accepted distance normalization, straight-loss subtraction, low-recirculation masks, and mesh/GCI admission.

The junction heat-loss evidence is real at role/accounting level for Salt2-4, but it is aggregate `junction_or_stub` heat transfer, not per-junction closure. Corner pressure-drop evidence exists and is directionally useful, but current K values are diagnostic upper bounds, not admitted component-K coefficients.

## Pressure Map Review

- Cases reviewed: `11`
- Branch rows reviewed: `66`
- Station rows reviewed: `330`
- Branch rows blocked by recirculation mask: `66`
- Fit-admitted pressure rows: `0`
- Static-vs-p_rgh branch delta sign differences in AGENT-457 rows: `24`

| case | branch rows | blocked | static/p_rgh sign diff | max reverse proxy | status |
|---|---:|---:|---:|---:|---|
| `salt1_hi10q` | 6 | 6 | 0 | 0.850 | diagnostic_location_pressure_map_only |
| `salt1_lo10q` | 6 | 6 | 0 | 0.846 | diagnostic_location_pressure_map_only |
| `salt1_nominal` | 6 | 6 | 0 | 0.849 | diagnostic_location_pressure_map_only |
| `salt2_hi5q` | 6 | 6 | 2 | 0.842 | diagnostic_location_pressure_map_only |
| `salt2_lo5q` | 6 | 6 | 2 | 0.845 | diagnostic_location_pressure_map_only |
| `salt2_mainline` | 6 | 6 | 2 | 0.845 | diagnostic_location_pressure_map_only |
| `salt3_mainline` | 6 | 6 | 4 | 0.836 | diagnostic_location_pressure_map_only |
| `salt4_hi5q` | 6 | 6 | 4 | 0.835 | diagnostic_location_pressure_map_only |
| `salt4_lo5q` | 6 | 6 | 4 | 0.835 | diagnostic_location_pressure_map_only |
| `salt4_mainline` | 6 | 6 | 4 | 0.835 | diagnostic_location_pressure_map_only |
| `val_salt2` | 6 | 6 | 2 | 0.840 | diagnostic_location_pressure_map_only |

## What Looks Physically Coherent

- Coverage is complete: every case has 30 stations and 6 branch rows.
- The branch labels map to the correct physical loop locations: `lower_leg` is heater, `right_leg` is downcomer, `upper_leg` is cooled top leg.
- Mainline Salt2/Salt3/Salt4 static branch means vary smoothly across the family rather than jumping randomly.
- Salt2 +/-5Q and `val_salt2` sit near `salt2_mainline`, which is a useful consistency check for the postprocessing path.

## What Does Not Support Closure Fitting Yet

- Absolute static pressure is gauge/reference sensitive and hydrostatic dominated; it is not a cross-case closure metric by itself.
- `p_rgh` deltas are the better hydraulic diagnostic, but the branch-level maps show static/p_rgh sign disagreements in several rows.
- The AGENT-449 admission table reports 66/66 branches blocked by material recirculation mask and 0 true `f_D` or component-`K` rows admitted.
- Upcomer/test-section branches are hybrid/recirculating lanes, not ordinary single-stream pipe-loss evidence.

## Junction Heat Loss

| case | role | realized W | direction | critique |
|---|---|---:|---|---|
| `salt_2` | `junction_other` | -39.128 | from_fluid | junction_or_stub_loss_is_observed_as_aggregate;not_split_by_four_junctions;radiation_included_in_total_wallHeatFlux |
| `salt_2` | `junction_segment_realized_wallflux` | -39.128 | from_fluid | same_path_present_but_realized_wallHeatFlux_is_forbidden_runtime_input;not_per_junction_resolved |
| `salt_3` | `junction_other` | -43.235 | from_fluid | junction_or_stub_loss_is_observed_as_aggregate;not_split_by_four_junctions;radiation_included_in_total_wallHeatFlux |
| `salt_3` | `junction_segment_realized_wallflux` | -43.235 | from_fluid | same_path_present_but_realized_wallHeatFlux_is_forbidden_runtime_input;not_per_junction_resolved |
| `salt_4` | `junction_other` | -48.485 | from_fluid | junction_or_stub_loss_is_observed_as_aggregate;not_split_by_four_junctions;radiation_included_in_total_wallHeatFlux |
| `salt_4` | `junction_segment_realized_wallflux` | -48.485 | from_fluid | same_path_present_but_realized_wallHeatFlux_is_forbidden_runtime_input;not_per_junction_resolved |

Interpretation: we understand that junction/stub surfaces remove nontrivial heat from the fluid in the realized CFD accounting. We do not yet understand it as a predictive per-junction closure because the evidence is aggregate, includes radiation in total `wallHeatFlux`, and is documented as diagnostic/non-predictive.

## Corner Pressure Drops

| corner | cases | mean K apparent | mean K local upper bound | status |
|---|---:|---:|---:|---|
| `corner_lower_left` | 3 | 8.269 | 3.453 | diagnostic_upper_bound_not_fit_admitted |
| `corner_lower_right` | 3 | 13.680 | 7.096 | diagnostic_upper_bound_not_fit_admitted |
| `corner_upper_right` | 3 | 14.611 | 6.973 | diagnostic_upper_bound_not_fit_admitted |
| `corner_upper_left` | 3 | 6.382 | 2.236 | diagnostic_upper_bound_not_fit_admitted |

Interpretation: corner pressure drops are identified and roughly quantified from preserved two-tap rows. The evidence supports the statement that corners contribute materially but do not dominate the hydraulic discrepancy: prior separation reduced phi by about 9-10% in heater/downcomer/cooler and about 21% on average in upcomer lanes. However, K values remain upper-bound diagnostics because the straight-loss subtraction uses an `abs(dz)` tap-length proxy, rows are coarse/no-GCI, and recirculation affects adjacent upcomer spans.

## Next Scientific Gates

1. For pressure closure: extract centerline-distance-normalized tap pairs, subtract straight losses with accepted geometry, use low-recirculation masks, and repeat on admitted mesh/GCI rows.
2. For junction heat: split `junction_other` into the four junction/stub surfaces, preserve radiation/convective components or explicitly document inseparability, and build setup-only predictive parameters without realized `wallHeatFlux` as runtime input.
3. For corner K: rerun two-tap corner extraction with full tap centerline lengths and mesh-refinement/GCI before admitting any component-K coefficients.
