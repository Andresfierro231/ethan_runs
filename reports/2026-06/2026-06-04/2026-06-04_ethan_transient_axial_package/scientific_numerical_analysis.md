# Scientific And Numerical Analysis

Generated: `2026-06-07T15:16:20-05:00`

## Scope

This report audits the transient and axial package from both a scientific and a numerical perspective.

## Axial extraction audit

- Full latest-time `T/Nu/q` patch extraction succeeded for `3` case(s).
- Partial latest-time field extraction succeeded for `0` case(s).
- `6` case(s) are currently q-only fallbacks because reconstructed `T` could not be read robustly by `foamPostProcess`.
- The recurring failure mode is a malformed reconstructed `T` file with a scalar read error. That is a postprocessing/readability issue, not evidence that the wallHeatFlux histories themselves are invalid.

## Scientific interpretation

- The transient products confirm that the strongest numerical steadiness evidence is in Salt 2, Salt 3, and Salt 4 Kirst; Salt 4 Jin remains usable but more cautionary; Salt 1 remains the weakest salt family on practical steady-state credibility.
- The axial q-based reductions remain scientifically useful even where reconstructed `T` fails. They still localize where heat is added, removed, and lost along each leg and they align with the section-transport conclusion that the upper leg and junction-region channels are the main remaining sensitivity areas.
- The metric-coverage audit matters: the active Salt 2 continuation has wallHeatFlux data deeper into time than the continued TP/TW histories, so thermal-balance claims can be fresher than probe-history claims for that case.

## Numerical interpretation

- Use `case_audit_summary.csv` for slope-based late-window checks. A small `last_window_slope_per_s` and a small late-time `Net total Q` support practical steady-state use, even if the coded convergence flag never fired.
- Use `metric_coverage_end_times.csv` before comparing tails across cases. Do not over-interpret one metric as if every metric extended to the same latest time.
- Treat axial `Nu` and patch-averaged wall temperature as conditional diagnostics until the reconstructed-`T` read path is made uniformly reliable.

## Representative groups

- `salt_test_1`: manuscript representative `none yet`; sensitivity set `viscosity_screening_salt_test_1_jin_coarse_mesh; viscosity_screening_salt_test_1_kirst_coarse_mesh`
- `salt_test_2`: manuscript representative `val_salt_test_2_coarse_mesh_laminar`; sensitivity set `val_salt_test_2_coarse_mesh_laminar; viscosity_screening_salt_test_2_jin_coarse_mesh; viscosity_screening_salt_test_2_kirst_coarse_mesh`
- `salt_test_3`: manuscript representative `viscosity_screening_salt_test_3_jin_coarse_mesh`; sensitivity set `viscosity_screening_salt_test_3_jin_coarse_mesh; viscosity_screening_salt_test_3_kirst_coarse_mesh`
- `salt_test_4`: manuscript representative `viscosity_screening_salt_test_4_jin_coarse_mesh`; sensitivity set `viscosity_screening_salt_test_4_jin_coarse_mesh; viscosity_screening_salt_test_4_kirst_coarse_mesh`

## Case-by-case audit

### `val_salt_test_2_coarse_mesh_laminar`

- Run state: `run_status=running`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`.
- Metric coverage ends: `mdot=1724.0` s, `TP mean=1724.0` s, `TW5=1724.0` s, `ambient proxy=3811.0` s, `total_Q=3811.0` s.
- Validation context: `exp_all_temp_rmse_k=5.195921279377687`, `exp_mdot_abs_error_pct=18.951017976190467`, `exp_q_external_loss_abs_error_pct=20.574219228738393`.
- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa=36.74926249`, `left_leg_abs_delta_p_rgh_pa=15.473324062`, `right_leg_abs_delta_p_rgh_pa=9.621540102`.
- Axial extraction: `status=q_only_fallback`, `patches_with_areaAverage_T=0`, `patches_with_areaAverage_Nu=0`.

### `viscosity_screening_salt_test_1_jin_coarse_mesh`

- Run state: `run_status=terminated`, `essential_steadiness_class=not_steady_enough`, `usable_for_steady_state_now=no`.
- Metric coverage ends: `mdot=3230.0` s, `TP mean=3230.0` s, `TW5=3230.0` s, `ambient proxy=3230.0` s, `total_Q=3230.0` s.
- Validation context: `exp_all_temp_rmse_k=17.745189678331162`, `exp_mdot_abs_error_pct=28.70387302215191`, `exp_q_external_loss_abs_error_pct=27.360108353568656`.
- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa=`, `left_leg_abs_delta_p_rgh_pa=`, `right_leg_abs_delta_p_rgh_pa=`.
- Axial extraction: `status=q_only_fallback`, `patches_with_areaAverage_T=0`, `patches_with_areaAverage_Nu=0`.

### `viscosity_screening_salt_test_1_kirst_coarse_mesh`

- Run state: `run_status=completed`, `essential_steadiness_class=not_steady_enough`, `usable_for_steady_state_now=no`.
- Metric coverage ends: `mdot=3279.163522013` s, `TP mean=3279.16352` s, `TW5=3279.16352` s, `ambient proxy=3279.163522` s, `total_Q=3279.163522` s.
- Validation context: `exp_all_temp_rmse_k=17.55620984679648`, `exp_mdot_abs_error_pct=30.809515537974686`, `exp_q_external_loss_abs_error_pct=27.346344175812238`.
- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa=`, `left_leg_abs_delta_p_rgh_pa=`, `right_leg_abs_delta_p_rgh_pa=`.
- Axial extraction: `status=q_only_fallback`, `patches_with_areaAverage_T=0`, `patches_with_areaAverage_Nu=0`.

### `viscosity_screening_salt_test_2_jin_coarse_mesh`

- Run state: `run_status=terminated`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`.
- Metric coverage ends: `mdot=2432.0` s, `TP mean=2432.0` s, `TW5=2432.0` s, `ambient proxy=2432.0` s, `total_Q=2432.0` s.
- Validation context: `exp_all_temp_rmse_k=5.622281562405422`, `exp_mdot_abs_error_pct=21.65710934523809`, `exp_q_external_loss_abs_error_pct=20.945467128832053`.
- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa=`, `left_leg_abs_delta_p_rgh_pa=`, `right_leg_abs_delta_p_rgh_pa=`.
- Axial extraction: `status=full_field_success`, `patches_with_areaAverage_T=49`, `patches_with_areaAverage_Nu=49`.

### `viscosity_screening_salt_test_2_kirst_coarse_mesh`

- Run state: `run_status=completed`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`.
- Metric coverage ends: `mdot=586.560240964` s, `TP mean=586.560241` s, `TW5=586.560241` s, `ambient proxy=586.560241` s, `total_Q=586.560241` s.
- Validation context: `exp_all_temp_rmse_k=6.140964304544514`, `exp_mdot_abs_error_pct=27.121653571428574`, `exp_q_external_loss_abs_error_pct=20.43851841298395`.
- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa=`, `left_leg_abs_delta_p_rgh_pa=`, `right_leg_abs_delta_p_rgh_pa=`.
- Axial extraction: `status=full_field_success`, `patches_with_areaAverage_T=49`, `patches_with_areaAverage_Nu=49`.

### `viscosity_screening_salt_test_3_jin_coarse_mesh`

- Run state: `run_status=terminated`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`.
- Metric coverage ends: `mdot=2515.0` s, `TP mean=2515.0` s, `TW5=2515.0` s, `ambient proxy=2515.0` s, `total_Q=2515.0` s.
- Validation context: `exp_all_temp_rmse_k=5.612608549444536`, `exp_mdot_abs_error_pct=14.711376500000014`, `exp_q_external_loss_abs_error_pct=19.009679138345895`.
- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa=38.022483570000006`, `left_leg_abs_delta_p_rgh_pa=15.213591897`, `right_leg_abs_delta_p_rgh_pa=9.653894862000001`.
- Axial extraction: `status=q_only_fallback`, `patches_with_areaAverage_T=0`, `patches_with_areaAverage_Nu=0`.

### `viscosity_screening_salt_test_3_kirst_coarse_mesh`

- Run state: `run_status=terminated`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`.
- Metric coverage ends: `mdot=3298.0` s, `TP mean=3298.0` s, `TW5=3298.0` s, `ambient proxy=3298.0` s, `total_Q=3298.0` s.
- Validation context: `exp_all_temp_rmse_k=5.458447708953641`, `exp_mdot_abs_error_pct=20.17977992857144`, `exp_q_external_loss_abs_error_pct=19.01950843267885`.
- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa=`, `left_leg_abs_delta_p_rgh_pa=`, `right_leg_abs_delta_p_rgh_pa=`.
- Axial extraction: `status=full_field_success`, `patches_with_areaAverage_T=49`, `patches_with_areaAverage_Nu=49`.

### `viscosity_screening_salt_test_4_jin_coarse_mesh`

- Run state: `run_status=terminated`, `essential_steadiness_class=borderline_but_usable`, `usable_for_steady_state_now=yes_with_caveat`.
- Metric coverage ends: `mdot=2083.0` s, `TP mean=2083.0` s, `TW5=2083.0` s, `ambient proxy=2083.0` s, `total_Q=2083.0` s.
- Validation context: `exp_all_temp_rmse_k=6.061627553731621`, `exp_mdot_abs_error_pct=15.496810024875622`, `exp_q_external_loss_abs_error_pct=17.40163440703854`.
- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa=38.42732622`, `left_leg_abs_delta_p_rgh_pa=15.272479906`, `right_leg_abs_delta_p_rgh_pa=11.055311839`.
- Axial extraction: `status=q_only_fallback`, `patches_with_areaAverage_T=0`, `patches_with_areaAverage_Nu=0`.

### `viscosity_screening_salt_test_4_kirst_coarse_mesh`

- Run state: `run_status=terminated`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`.
- Metric coverage ends: `mdot=2984.0` s, `TP mean=2984.0` s, `TW5=2984.0` s, `ambient proxy=2984.0` s, `total_Q=2984.0` s.
- Validation context: `exp_all_temp_rmse_k=5.908171197457817`, `exp_mdot_abs_error_pct=20.999207201492545`, `exp_q_external_loss_abs_error_pct=17.45227379771527`.
- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa=`, `left_leg_abs_delta_p_rgh_pa=`, `right_leg_abs_delta_p_rgh_pa=`.
- Axial extraction: `status=q_only_fallback`, `patches_with_areaAverage_T=0`, `patches_with_areaAverage_Nu=0`.

## Recommended next analytical moves

- Keep using the q-based axial products immediately; they are already strong enough for manuscript-facing discussion of where heat is added, removed, and lost.
- Treat `T/Nu`-based axial interpretation as a second-stage refinement that needs a cleaner reconstructed-field path, likely on a compute-node postprocessing route or with a more targeted reconstruction workflow.
- Pair `metric_coverage_end_times.csv` with `case_audit_summary.csv` whenever late-time behavior is discussed so the numerical evidence is honest about mixed metric horizons.
