# salt1_lo10q Streamwise Pressure / 1D Map

## Provenance

- Source case: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation`
- Harvest package: `AGENT-447_expanded_salt_pressure_ladder_8pm_sbatch`
- Harvest job ID: `3297863`
- Station CSV: `work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/station_pressure_ladder.csv`
- Source ID: `viscosity_screening_salt_test_1_jin_coarse_mesh`
- Time: `8016` s
- Window: `7416-8016`
- Split role: `training_perturbation`
- Admission caveat: Salt1 -10%Q training candidate; pressure ladder diagnostic until mesh/GCI and pressure gates admit

## Branch Average Pressures

| CFD span | Physical location | 1D segment(s) | flow stations | avg p [Pa] | avg p_rgh [Pa] | end-start p [Pa] | max reverse proxy |
|---|---|---|---|---:|---:|---:|---:|
| lower_leg | heater / bottom heated incline | `heated_incline` | lower_leg__s04 -> lower_leg__s00 | -6416.369 | -2.804 | -7159.770 | 0.5406 |
| left_lower_leg | lower upcomer below test section | `left_lower_vertical` | left_lower_leg__s00 -> left_lower_leg__s04 | -3324.418 | -8.884 | -4753.199 | 0.6701 |
| test_section_span | test section / middle upcomer | `test_section` | test_section_span__s00 -> test_section_span__s04 | -8725.466 | -11.126 | 3842.982 | 0.4440 |
| left_upper_leg | upper upcomer above test section | `left_upper_vertical` | left_upper_leg__s00 -> left_upper_leg__s04 | -14610.388 | -11.486 | -5558.156 | 0.8462 |
| upper_leg | cooled leg / top cooled incline | `top_horizontal_inlet;cooled_incline_pre_hx;cooled_incline_hx_active;cooled_incline_post_hx;top_horizontal_exit` | upper_leg__s00 -> upper_leg__s04 | -7421.812 | -7.888 | 7026.788 | 0.5783 |
| right_leg | right downcomer / cold vertical return | `right_vertical` | right_leg__s00 -> right_leg__s04 | -4461.150 | -9.119 | -14201.376 | 0.6701 |

## Labeling Guardrails

- `lower_leg` = heater = 1D `heated_incline`; loop-flow order `s04 -> s00`.
- `right_leg` = downcomer = 1D `right_vertical`; loop-flow order `s00 -> s04`.
- `upper_leg` = cooled top leg = Fluid top/HX composite including `cooled_incline_hx_active`.
- These rows are diagnostic harvested pressure averages, not admitted `f_D` or component-`K` coefficients.
