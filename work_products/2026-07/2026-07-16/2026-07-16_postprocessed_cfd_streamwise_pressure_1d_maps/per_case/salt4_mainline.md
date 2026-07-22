# salt4_mainline Streamwise Pressure / 1D Map

## Provenance

- Source case: `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation`
- Harvest package: `AGENT-445_pressure_ladder_unlock_sbatch`
- Harvest job ID: `3297860`
- Station CSV: `work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/station_pressure_ladder.csv`
- Source ID: `viscosity_screening_salt_test_4_jin_coarse_mesh`
- Time: `10000` s
- Window: `not declared in source CSV`
- Split role: `holdout_or_training_by_declared_scorecard`
- Admission caveat: Mainline Salt4 pressure ladder diagnostic until mesh/GCI and pressure gates admit.

## Branch Average Pressures

| CFD span | Physical location | 1D segment(s) | flow stations | avg p [Pa] | avg p_rgh [Pa] | end-start p [Pa] | max reverse proxy |
|---|---|---|---|---:|---:|---:|---:|
| lower_leg | heater / bottom heated incline | `heated_incline` | lower_leg__s04 -> lower_leg__s00 | -6272.423 | 9.249 | -7008.156 | 0.5406 |
| left_lower_leg | lower upcomer below test section | `left_lower_vertical` | left_lower_leg__s00 -> left_lower_leg__s04 | -3246.359 | -1.428 | -4651.347 | 0.5929 |
| test_section_span | test section / middle upcomer | `test_section` | test_section_span__s00 -> test_section_span__s04 | -8532.711 | 3.200 | 3762.237 | 0.3436 |
| left_upper_leg | upper upcomer above test section | `left_upper_vertical` | left_upper_leg__s00 -> left_upper_leg__s04 | -14293.193 | 1.486 | -5440.895 | 0.8346 |
| upper_leg | cooled leg / top cooled incline | `top_horizontal_inlet;cooled_incline_pre_hx;cooled_incline_hx_active;cooled_incline_post_hx;top_horizontal_exit` | upper_leg__s00 -> upper_leg__s04 | -7257.033 | 2.601 | 6879.619 | 0.6107 |
| right_leg | right downcomer / cold vertical return | `right_vertical` | right_leg__s00 -> right_leg__s04 | -4359.051 | 0.790 | -13900.425 | 0.6757 |

## Labeling Guardrails

- `lower_leg` = heater = 1D `heated_incline`; loop-flow order `s04 -> s00`.
- `right_leg` = downcomer = 1D `right_vertical`; loop-flow order `s00 -> s04`.
- `upper_leg` = cooled top leg = Fluid top/HX composite including `cooled_incline_hx_active`.
- These rows are diagnostic harvested pressure averages, not admitted `f_D` or component-`K` coefficients.
