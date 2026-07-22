# salt1_hi10q Streamwise Pressure / 1D Map

## Provenance

- Source case: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation`
- Harvest package: `AGENT-447_expanded_salt_pressure_ladder_8pm_sbatch`
- Harvest job ID: `3297863`
- Station CSV: `work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/station_pressure_ladder.csv`
- Source ID: `viscosity_screening_salt_test_1_jin_coarse_mesh`
- Time: `5587` s
- Window: `4987-5587`
- Split role: `training_perturbation`
- Admission caveat: Salt1 +10%Q training candidate with documented conflict-resolution caveat; pressure ladder diagnostic until gates admit

## Branch Average Pressures

| CFD span | Physical location | 1D segment(s) | flow stations | avg p [Pa] | avg p_rgh [Pa] | end-start p [Pa] | max reverse proxy |
|---|---|---|---|---:|---:|---:|---:|
| lower_leg | heater / bottom heated incline | `heated_incline` | lower_leg__s04 -> lower_leg__s00 | -6396.302 | -0.974 | -7138.273 | 0.5406 |
| left_lower_leg | lower upcomer below test section | `left_lower_vertical` | left_lower_leg__s00 -> left_lower_leg__s04 | -3313.252 | -8.109 | -4738.655 | 0.6597 |
| test_section_span | test section / middle upcomer | `test_section` | test_section_span__s00 -> test_section_span__s04 | -8698.255 | -9.175 | 3831.985 | 0.3533 |
| left_upper_leg | upper upcomer above test section | `left_upper_vertical` | left_upper_leg__s00 -> left_upper_leg__s04 | -14565.772 | -10.842 | -5541.268 | 0.8500 |
| upper_leg | cooled leg / top cooled incline | `top_horizontal_inlet;cooled_incline_pre_hx;cooled_incline_hx_active;cooled_incline_post_hx;top_horizontal_exit` | upper_leg__s00 -> upper_leg__s04 | -7398.537 | -6.231 | 7005.221 | 0.5783 |
| right_leg | right downcomer / cold vertical return | `right_vertical` | right_leg__s00 -> right_leg__s04 | -4446.670 | -7.911 | -14159.168 | 0.6736 |

## Labeling Guardrails

- `lower_leg` = heater = 1D `heated_incline`; loop-flow order `s04 -> s00`.
- `right_leg` = downcomer = 1D `right_vertical`; loop-flow order `s00 -> s04`.
- `upper_leg` = cooled top leg = Fluid top/HX composite including `cooled_incline_hx_active`.
- These rows are diagnostic harvested pressure averages, not admitted `f_D` or component-`K` coefficients.
