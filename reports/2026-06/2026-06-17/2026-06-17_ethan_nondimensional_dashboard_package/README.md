# Ethan Nondimensional Dashboard Package

Generated: `2026-06-17T14:51:33-05:00`

## Purpose

This package is a first dashboard and quick-spec layer for later reduced-order correlation work on Ethan CFD runs.
It separates water and salt families, inventories the starting and boundary conditions already present in the repo,
publishes late-window bulk-temperature summaries for the main loop regions, and assembles candidate lower-dimensional inputs
for later effective friction-factor and effective HTC correlation work.

## Theory, semantics, and scope boundaries

- Effective friction factor is treated here as a later derived loop/leg indicator from CFD support data, not as a primitive solver input.
- Effective HTC, `UA'`, and related thermal-resistance quantities are treated as support-gated effective transfer indicators rather than intrinsic local closure coefficients.
- The cooler metadata field `cooler_h_W_m2K` is retained as a setup descriptor because it is useful for screening, but the readable 3D `0/T` implementation is still a fixed-`Q` cooling sink and not a clean resolved cooler-side convective coefficient.
- The temperature dashboard values are late-window bulk-fluid summaries built from retained cut-plane bulk-temperature bins, not instantaneous one-timestep snapshots.
- Initial hydraulic state is not cleanly published in the canonical Ethan metadata index, so this package records that gap explicitly and uses late-window circulation strength (`mdot_mean_abs_kg_s`) as the reusable hydraulic context field.

## Data sources

- Metadata index: `reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`
- Heat audit latest/late-window tables: `reports/2026-06-09_ethan_steady_state_heat_flow_audit/latest_heat_partition.csv` and `reports/2026-06-09_ethan_steady_state_heat_flow_audit/heat_window_summary.csv`
- All-runs field-transport campaign provenance: `reports/2026-06-15_ethan_all_runs_field_transport_campaign/README.md`
- Boundary-modeling caveats: `reports/2026-06-15_ethan_boundary_modeling_report/README.md`
- Late-window temperature reductions come from the June 15 live case-analysis package roots listed in `summary.json` and the import manifest.

## Temperature method

- Span and branch temperatures use the retained cut-plane bulk-temperature samples in `raw_extraction/bulk_cross_section_temperature_samples.csv` from the selected June 15 live case-analysis package for each case.
- The preferred bulk metric is `bulk_temp_flow_weighted_k`; if it is unavailable for a row, the reduction falls back to area-average bulk temperature.
- Within each retained time, rows are weighted by positive aligned mass flux when available, otherwise by cut-plane area.
- The published temperature is then the mean across the retained late-window times advertised by that package's `summary.json`.
- The derived branches are: heater=`lower_leg`, downcomer=`right_leg`, upcomer=`left_lower_leg + test_section_span + left_upper_leg`, cooler=`upper_leg`.

## Salt dashboard

| Case | Run status | T_init [K] | Heater [W] | Cooling [W] | Insulation [in] | |mdot| [kg/s] | Max branch dT [K] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Salt 2 Val | running | 451.5 | 265.7 | 56.34 | 1.65 | 0.01361622898 | 7.36 |
| Salt 1 Jin | terminated | 440.0 | 232.3 | 55.58 | 1.4 | 0.0112647880625 | 8.24 |
| Salt 1 Kirst | completed | 440.0 | 232.3 | 55.58 | 1.4 | 0.010932096545 | 8.45 |
| Salt 2 Jin | terminated | 447.0 | 265.7 | 56.34 | 1.4 | 0.01316160563 | 7.60 |
| Salt 2 Kirst | completed | 447.0 | 265.7 | 56.34 | 1.4 | 0.012243562199999999 | 8.07 |
| Salt 3 Jin | terminated | 459.0 | 297.5 | 60.55 | 1.4 | 0.014925509112499999 | 7.53 |
| Salt 3 Kirst | terminated | 459.0 | 297.5 | 60.55 | 1.4 | 0.0139685385125 | 7.97 |
| Salt 4 Jin | terminated | 475.0 | 337.6 | 65.98 | 1.4 | 0.016985141185 | 7.47 |
| Salt 4 Kirst | terminated | 475.0 | 337.6 | 65.98 | 1.4 | 0.0158791593525 | 7.99 |

- Outer insulation spans `1.40` to `1.65` in across this family.
- The late-window max branch bulk-temperature spread spans `7.36` to `8.45` K.
- The late-window ambient-proxy fraction spans `0.703` to `0.724` of heater power.
- Highest reported case-average probe temperature is `Salt 4 Jin` at `477.38` K.

## Water dashboard

| Case | Run status | T_init [K] | Heater [W] | Cooling [W] | Insulation [in] | |mdot| [kg/s] | Max branch dT [K] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Water 1 | terminated | 314.515625 | 58.8 | 26.86 | 0.4 | 0.00650637830175 | 1.22 |
| Water 2 | terminated | 320.26374999999996 | 77.6 | 35.63 | 0.4 | 0.007834229101 | 1.33 |
| Water 3 | terminated | 324.390625 | 93.0 | 43.02 | 0.4 | 0.008932687613 | 1.36 |
| Water 4 | terminated | 334.15375 | 129.0 | 58.06 | 0.4 | 0.0108710076475 | 1.45 |

- Outer insulation spans `0.40` to `0.40` in across this family.
- The late-window max branch bulk-temperature spread spans `1.22` to `1.45` K.
- The late-window ambient-proxy fraction spans `0.448` to `0.462` of heater power.
- Highest reported case-average probe temperature is `Water 4` at `334.89` K.

## Artifacts

- `salt_dashboard.csv`: `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_dashboard.csv`
- `water_dashboard.csv`: `reports/2026-06-17_ethan_nondimensional_dashboard_package/water_dashboard.csv`
- `salt_candidate_correlation_inputs.csv`: `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_candidate_correlation_inputs.csv`
- `water_candidate_correlation_inputs.csv`: `reports/2026-06-17_ethan_nondimensional_dashboard_package/water_candidate_correlation_inputs.csv`
- `summary.json`: `reports/2026-06-17_ethan_nondimensional_dashboard_package/summary.json`
- `salt_dashboard_overview`: `reports/2026-06-17_ethan_nondimensional_dashboard_package/figures/png/salt_dashboard_overview.png`
- `water_dashboard_overview`: `reports/2026-06-17_ethan_nondimensional_dashboard_package/figures/png/water_dashboard_overview.png`

## Recommended next derived quantities

- Add case- and leg-level effective friction scalars once the separate friction-factor/minor-loss work is ready.
- Add late-temperature fluid-property snapshots and family-specific Reynolds/Prandtl-style groups only after deciding the exact property-evaluation convention to use.
- Keep salt and water as separate fitting families unless a later audit shows that a shared nondimensionalization truly collapses the two sets.
