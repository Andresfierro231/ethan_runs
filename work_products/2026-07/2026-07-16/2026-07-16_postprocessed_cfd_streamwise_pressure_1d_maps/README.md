# Postprocessed CFD Streamwise Pressure / 1D Maps

This package generalizes the Salt2 pressure/1D map across all currently available harvested station-pressure ladder outputs.
No solver outputs were mutated and no scheduler jobs were submitted.

## Scope

- Cases mapped: `11`
- Station rows: `330`
- Branch-average rows: `66`
- Sources: AGENT-445 job `3297860` and AGENT-447 job `3297863`.

## Provenance By Case

| case_key | split role | harvest job | time s | source case |
|---|---|---:|---:|---|
| `salt1_hi10q` | `training_perturbation` | `3297863` | 5587 | `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation` |
| `salt1_lo10q` | `training_perturbation` | `3297863` | 8016 | `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation` |
| `salt1_nominal` | `training` | `3297863` | 7884 | `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation` |
| `salt2_hi5q` | `holdout_perturbation` | `3297863` | 9780 | `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt2_jin_hi5q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation` |
| `salt2_lo5q` | `holdout_perturbation` | `3297863` | 10275 | `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt2_jin_lo5q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation` |
| `salt2_mainline` | `training` | `3297860` | 7915 | `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation` |
| `salt3_mainline` | `validation_or_training_by_declared_scorecard` | `3297860` | 7618 | `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation` |
| `salt4_hi5q` | `training_perturbation` | `3297863` | 11399 | `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_hi5q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation` |
| `salt4_lo5q` | `training_perturbation` | `3297863` | 11695 | `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_lo5q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation` |
| `salt4_mainline` | `holdout_or_training_by_declared_scorecard` | `3297860` | 10000 | `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation` |
| `val_salt2` | `external_validation` | `3297863` | 8602 | `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation` |

## Branch Mean Static Pressure By Case

| case_key | lower_leg heater | left_lower upcomer | test_section | left_upper upcomer | upper_leg cooler | right_leg downcomer |
|---|---:|---:|---:|---:|---:|---:|
| `salt1_hi10q` | -6396.302 | -3313.252 | -8698.255 | -14565.772 | -7398.537 | -4446.670 |
| `salt1_lo10q` | -6416.369 | -3324.418 | -8725.466 | -14610.388 | -7421.812 | -4461.150 |
| `salt1_nominal` | -6396.562 | -3313.401 | -8698.625 | -14566.524 | -7398.927 | -4446.891 |
| `salt2_hi5q` | -6338.727 | -3281.494 | -8621.984 | -14441.491 | -7333.276 | -4405.554 |
| `salt2_lo5q` | -6350.608 | -3287.850 | -8637.870 | -14467.713 | -7346.805 | -4413.948 |
| `salt2_mainline` | -6344.227 | -3284.413 | -8629.364 | -14453.701 | -7339.549 | -4409.427 |
| `salt3_mainline` | -6310.501 | -3266.385 | -8584.168 | -14379.015 | -7301.028 | -4385.680 |
| `salt4_hi5q` | -6267.780 | -3244.351 | -8526.370 | -14281.818 | -7251.611 | -4356.102 |
| `salt4_lo5q` | -6278.824 | -3249.862 | -8541.312 | -14307.280 | -7264.443 | -4363.652 |
| `salt4_mainline` | -6272.423 | -3246.359 | -8532.711 | -14293.193 | -7257.033 | -4359.051 |
| `val_salt2` | -6331.116 | -3277.370 | -8611.815 | -14424.841 | -7324.631 | -4400.182 |

## Mapping Guardrails

- `lower_leg` is the physical heater and maps to Fluid `heated_incline`; use station order `s04 -> s00`.
- `right_leg` is the physical downcomer and maps to Fluid `right_vertical`; use station order `s00 -> s04`.
- `upper_leg` is the cooled top leg and maps to `top_horizontal_inlet;cooled_incline_pre_hx;cooled_incline_hx_active;cooled_incline_post_hx;top_horizontal_exit`.
- `left_lower_leg -> test_section_span -> left_upper_leg` maps to `left_lower_vertical -> test_section -> left_upper_vertical`.
- Use `mean_p_Pa` for the static pressure value and preserve `mean_p_rgh_Pa` as the OpenFOAM gravity-adjusted diagnostic.
- All rows remain diagnostic pressure-map evidence until pressure definition, straight-loss subtraction, recirculation masking, and mesh/GCI gates are satisfied together.
