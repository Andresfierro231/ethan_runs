# Scientific Writeup Notes

## Observed outputs

- Transient mdot, probe-temperature, wall-temperature, and wall-heat histories now exist in a single report package for every salt case.
- Latest-time axial patch rows now carry ordered wall-heat, wall-temperature, and Nusselt summaries for each loop leg.
- Pressure-drop interpretation still comes from the separate section-transport package, where the upper leg dominates `|Delta p_rgh|` among use-ready Salt 2-4 rows.

## Inferred interpretation

- Jin-vs-Kirst differences remain strongest in flow and upper-leg resistance behavior, not in the shared ambient-loss bias.
- The transient heat-balance tail can now be inspected per section and per wall patch, which is the right way to test the collaborator's claim that slow net-heat decay is the main barrier to practical convergence.
- The axial latest-time rows are suitable for a first scientific writeup on where heat is added, removed, and lost along each leg, even though the axial coordinate is currently patch progress rather than geometric arc length.

## Representative-case reminders

- `val_salt_test_2_coarse_mesh_laminar`: `base_case_id=salt_test_2`, `variant_label=`, `run_status=running`, `usable_for_steady_state_now=yes`, `exp_all_temp_rmse_k=5.195921279377687`, `exp_mdot_abs_error_pct=18.951017976190467`
- `viscosity_screening_salt_test_1_jin_coarse_mesh`: `base_case_id=salt_test_1`, `variant_label=jin`, `run_status=terminated`, `usable_for_steady_state_now=no`, `exp_all_temp_rmse_k=17.745189678331162`, `exp_mdot_abs_error_pct=28.70387302215191`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh`: `base_case_id=salt_test_1`, `variant_label=kirst`, `run_status=completed`, `usable_for_steady_state_now=no`, `exp_all_temp_rmse_k=17.55620984679648`, `exp_mdot_abs_error_pct=30.809515537974686`
- `viscosity_screening_salt_test_2_jin_coarse_mesh`: `base_case_id=salt_test_2`, `variant_label=jin`, `run_status=terminated`, `usable_for_steady_state_now=yes`, `exp_all_temp_rmse_k=5.622281562405422`, `exp_mdot_abs_error_pct=21.65710934523809`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh`: `base_case_id=salt_test_2`, `variant_label=kirst`, `run_status=completed`, `usable_for_steady_state_now=yes`, `exp_all_temp_rmse_k=6.140964304544514`, `exp_mdot_abs_error_pct=27.121653571428574`
- `viscosity_screening_salt_test_3_jin_coarse_mesh`: `base_case_id=salt_test_3`, `variant_label=jin`, `run_status=terminated`, `usable_for_steady_state_now=yes`, `exp_all_temp_rmse_k=5.612608549444536`, `exp_mdot_abs_error_pct=14.711376500000014`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh`: `base_case_id=salt_test_3`, `variant_label=kirst`, `run_status=terminated`, `usable_for_steady_state_now=yes`, `exp_all_temp_rmse_k=5.458447708953641`, `exp_mdot_abs_error_pct=20.17977992857144`
- `viscosity_screening_salt_test_4_jin_coarse_mesh`: `base_case_id=salt_test_4`, `variant_label=jin`, `run_status=terminated`, `usable_for_steady_state_now=yes_with_caveat`, `exp_all_temp_rmse_k=6.061627553731621`, `exp_mdot_abs_error_pct=15.496810024875622`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh`: `base_case_id=salt_test_4`, `variant_label=kirst`, `run_status=terminated`, `usable_for_steady_state_now=yes`, `exp_all_temp_rmse_k=5.908171197457817`, `exp_mdot_abs_error_pct=20.999207201492545`

## Next suggested actions

- Extend this package with sampled transient pressure reconstruction if the manuscript needs section pressure-drop evolution instead of latest-time ranking only.
- If a true `h(x)` with geometric distance is required, add a centerline-aware mesh extraction step rather than back-solving it from patch order.
