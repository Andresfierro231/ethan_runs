# Salt Model Dependency Handoff

## Purpose

This note is written for a future model builder. It states exactly which Salt
rows are defensible for downstream dependency use today, which rows are still
screening-only, and why.

## Final recommended Salt friction dependency

- Status: `provisional_defended`
- Recommended model label: `class_aware_re_power_law`
- Fit-used straight-section row count: `12`
- Feature `K_eff`: `not defensible yet`

Why the feature model is blocked:

- The preserved feature path only carries residual `p_rgh` subtraction.
- No dedicated feature-path hydro integral survived in the additive artifacts.
- Positive residual feature loss is therefore not enough to justify a minor-loss
  coefficient fit.

## Final recommended Salt HTC/Nu dependency

- Status: `not_defensible_yet`
- Recommended model label: `exploratory_screened_only_model`
- Defended thermal fit-used row count: `1`
- Screened-only sensitivity rows: `35`

Important interpretation boundary:

- `right_leg` remains excluded by the branch trust gate.
- `upcomer` remains sensitivity-only because it overlaps the direct component
  spans and would double-count geometry in any defended fit.

## Exact rows used

### Hydraulic fit-used rows

- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `test_section_span` / `Re=97.541` / `f=46.163`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `test_section_span` / `Re=80.347` / `f=53.574`
- `val_salt_test_2_coarse_mesh_laminar` / `lower_leg` / `Re=92.589` / `f=2.725`
- `val_salt_test_2_coarse_mesh_laminar` / `test_section_span` / `Re=108.360` / `f=42.366`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `lower_leg` / `Re=110.264` / `f=2.183`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `test_section_span` / `Re=128.738` / `f=35.231`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh` / `lower_leg` / `Re=91.269` / `f=2.523`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh` / `test_section_span` / `Re=105.918` / `f=40.523`
- `viscosity_screening_salt_test_4_jin_coarse_mesh` / `lower_leg` / `Re=150.192` / `f=1.664`
- `viscosity_screening_salt_test_4_jin_coarse_mesh` / `test_section_span` / `Re=173.736` / `f=26.715`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh` / `lower_leg` / `Re=121.565` / `f=1.847`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh` / `test_section_span` / `Re=140.402` / `f=30.668`

### Thermal fit-used rows

- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `left_lower_leg` / `Re=76.233` / `Nu=3.231`

## Exact rows excluded

### Feature rows

- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `corner_lower_left` -> `nonpositive_residual_feature_loss`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `corner_lower_right` -> `nonpositive_residual_feature_loss`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `corner_upper_left` -> `feature_pressure_method_residual_only`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `corner_upper_right` -> `feature_pressure_method_residual_only`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `test_section_complex` -> `nonpositive_residual_feature_loss`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `corner_lower_left` -> `nonpositive_residual_feature_loss`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `corner_lower_right` -> `nonpositive_residual_feature_loss`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `corner_upper_left` -> `feature_pressure_method_residual_only`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `corner_upper_right` -> `feature_pressure_method_residual_only`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `test_section_complex` -> `nonpositive_residual_feature_loss`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `corner_lower_left` -> `nonpositive_residual_feature_loss`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `corner_lower_right` -> `nonpositive_residual_feature_loss`

### Thermal exclusions

- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `left_lower_leg` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `left_upper_leg` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `lower_leg` -> `thermal_low_usable_fraction`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `right_leg` -> `right_leg_blocked_by_policy`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `test_section_span` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `upcomer` -> `derived_branch_overlap_double_counting`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `upper_leg` -> `thermal_support_marginal`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `left_lower_leg` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `left_upper_leg` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `lower_leg` -> `thermal_low_usable_fraction`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `right_leg` -> `right_leg_blocked_by_policy`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `test_section_span` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `upcomer` -> `derived_branch_overlap_double_counting`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `upper_leg` -> `thermal_support_marginal`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `left_lower_leg` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `left_upper_leg` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `lower_leg` -> `thermal_support_marginal`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `right_leg` -> `right_leg_blocked_by_policy`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `test_section_span` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `upcomer` -> `derived_branch_overlap_double_counting`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `upper_leg` -> `thermal_support_marginal`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `left_upper_leg` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `lower_leg` -> `thermal_support_marginal`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `right_leg` -> `right_leg_blocked_by_policy`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `test_section_span` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `upcomer` -> `derived_branch_overlap_double_counting`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `upper_leg` -> `thermal_support_marginal`
- `val_salt_test_2_coarse_mesh_laminar` / `left_lower_leg` -> `enthalpy_wall_heat_balance_loose`
- `val_salt_test_2_coarse_mesh_laminar` / `left_upper_leg` -> `enthalpy_wall_heat_balance_loose`
- `val_salt_test_2_coarse_mesh_laminar` / `lower_leg` -> `thermal_support_marginal`
- `val_salt_test_2_coarse_mesh_laminar` / `right_leg` -> `right_leg_blocked_by_policy`
- `val_salt_test_2_coarse_mesh_laminar` / `test_section_span` -> `enthalpy_wall_heat_balance_loose`
- `val_salt_test_2_coarse_mesh_laminar` / `upcomer` -> `derived_branch_overlap_double_counting`
- `val_salt_test_2_coarse_mesh_laminar` / `upper_leg` -> `thermal_small_delta_t`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `left_lower_leg` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `left_upper_leg` -> `enthalpy_wall_heat_balance_loose`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `lower_leg` -> `thermal_support_marginal`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `right_leg` -> `right_leg_blocked_by_policy`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `test_section_span` -> `enthalpy_wall_heat_balance_l

## Assumptions

- Salt `cp(T)` is effectively constant in the native case configurations, so the
  preserved bulk-temperature definition is compatible with `rho*u*cp` weighting.
- Branch-level intended versus parasitic heat separation depends on the current
  thermal-role metadata and remains a bounded decomposition, not a material
  resistance split.
- Positive `Nu` and positive apparent Darcy factor are required for defended
  fits; screened-only or sign-ambiguous rows remain out of the final dependency.

## Uncertainty

- Friction uncertainty comes mainly from small sample count and class separation
  between `lower_leg` and `test_section_span`.
- Thermal uncertainty comes mainly from weak branchwise enthalpy closure even
  where support-gated effective HTC looks numerically clean.
- Sensitivity conclusions are summarized in `sensitivity_summary.csv`.

## Sensitivity conclusions

- `hydraulic` / `direct_to_shear_gate_loose`: rows `12` -> `12`, qualitative change `no`. Loose direct/shear ratio gate 0.40-2.50.
- `hydraulic` / `direct_to_shear_gate_strict`: rows `12` -> `6`, qualitative change `yes`. Strict direct/shear ratio gate 0.67-1.50.
- `thermal` / `closure_gate_loose`: rows `1` -> `2`, qualitative change `yes`. Loose thermal closure gate: support>=0.85, |Twall-Tbulk|min>=0.25 K, residual<=0.30.
- `thermal` / `closure_gate_strict`: rows `1` -> `0`, qualitative change `yes`. Strict thermal closure gate: support>=0.95, |Twall-Tbulk|min>=0.75 K, residual<=0.10.
- `thermal` / `property_convention_case_probe`: rows `27` -> `27`, qualitative change `no`. Case-probe property convention uses probe_T_avg_K rather than branch bulk temperature when deriving Re and Nu.
- `thermal` / `late_window_latest_section_target`: rows `27` -> `27`, qualitative change `yes`. Latest-section target sensitivity swaps the late-window branch HTC/Nu target for the preserved latest section-summary target while keeping the same screened direct-branch support gate.
- `hydraulic` / `late_window_choice`: rows `12` -> `12`, qualitative change `unknown`. Hydro-corrected section closures are only preserved as time-mean rows in the additive package; no raw feature/path hydro timeseries survived for a true hydraulic late-window rerun.

## Water-family extension plan

1. Replicate the same provenance map and closure-gating structure for water.
2. Preserve the same distinction between defended rows, screened-only rows, and
   sensitivity-only rows.
3. Do not publish a combined water+salt dependency until feature-hydraulic and
   thermal-residual gates are equivalently resolved on the water side.
