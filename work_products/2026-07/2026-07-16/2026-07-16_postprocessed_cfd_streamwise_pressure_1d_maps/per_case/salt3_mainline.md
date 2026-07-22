# salt3_mainline Streamwise Pressure / 1D Map

## Provenance

- Source case: `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation`
- Harvest package: `AGENT-445_pressure_ladder_unlock_sbatch`
- Harvest job ID: `3297860`
- Station CSV: `work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/station_pressure_ladder.csv`
- Source ID: `viscosity_screening_salt_test_3_jin_coarse_mesh`
- Time: `7618` s
- Window: `not declared in source CSV`
- Split role: `validation_or_training_by_declared_scorecard`
- Admission caveat: Mainline Salt3 pressure ladder diagnostic until mesh/GCI and pressure gates admit.

## Branch Average Pressures

| CFD span | Physical location | 1D segment(s) | flow stations | avg p [Pa] | avg p_rgh [Pa] | end-start p [Pa] | max reverse proxy |
|---|---|---|---|---:|---:|---:|---:|
| lower_leg | heater / bottom heated incline | `heated_incline` | lower_leg__s04 -> lower_leg__s00 | -6310.501 | 7.689 | -7050.107 | 0.5406 |
| left_lower_leg | lower upcomer below test section | `left_lower_vertical` | left_lower_leg__s00 -> left_lower_leg__s04 | -3266.385 | -2.098 | -4679.187 | 0.6128 |
| test_section_span | test section / middle upcomer | `test_section` | test_section_span__s00 -> test_section_span__s04 | -8584.168 | 0.906 | 3784.469 | 0.3417 |
| left_upper_leg | upper upcomer above test section | `left_upper_vertical` | left_upper_leg__s00 -> left_upper_leg__s04 | -14379.015 | -0.229 | -5473.424 | 0.8362 |
| upper_leg | cooled leg / top cooled incline | `top_horizontal_inlet;cooled_incline_pre_hx;cooled_incline_hx_active;cooled_incline_post_hx;top_horizontal_exit` | upper_leg__s00 -> upper_leg__s04 | -7301.028 | 1.410 | 6920.467 | 0.5891 |
| right_leg | right downcomer / cold vertical return | `right_vertical` | right_leg__s00 -> right_leg__s04 | -4385.680 | -0.524 | -13983.016 | 0.6718 |

## Labeling Guardrails

- `lower_leg` = heater = 1D `heated_incline`; loop-flow order `s04 -> s00`.
- `right_leg` = downcomer = 1D `right_vertical`; loop-flow order `s00 -> s04`.
- `upper_leg` = cooled top leg = Fluid top/HX composite including `cooled_incline_hx_active`.
- These rows are diagnostic harvested pressure averages, not admitted `f_D` or component-`K` coefficients.
