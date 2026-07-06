# Salt Model Dependency Handoff v2

## Straight-section friction

- status: `provisional_defended`
- model: `class_aware_re_power_law`
- fit-used rows: `12`

## Feature K_eff

- status: `provisional_defended`
- model: `feature_name_aware_re_power_law`
- fit-used rows: `16`

## Salt HTC/Nu

- status: `not_defensible_yet`
- model: `exploratory_screened_only_model`
- fit-used rows: `2`

## Exact fit-used hydraulic rows

- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `straight_section_friction` / `test_section_span` / `Re=97.541` / `target=46.163`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `straight_section_friction` / `test_section_span` / `Re=80.347` / `target=53.574`
- `val_salt_test_2_coarse_mesh_laminar` / `straight_section_friction` / `lower_leg` / `Re=92.589` / `target=2.725`
- `val_salt_test_2_coarse_mesh_laminar` / `straight_section_friction` / `test_section_span` / `Re=108.360` / `target=42.366`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `straight_section_friction` / `lower_leg` / `Re=110.264` / `target=2.183`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `straight_section_friction` / `test_section_span` / `Re=128.738` / `target=35.231`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh` / `straight_section_friction` / `lower_leg` / `Re=91.269` / `target=2.523`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh` / `straight_section_friction` / `test_section_span` / `Re=105.918` / `target=40.523`
- `viscosity_screening_salt_test_4_jin_coarse_mesh` / `straight_section_friction` / `lower_leg` / `Re=150.192` / `target=1.664`
- `viscosity_screening_salt_test_4_jin_coarse_mesh` / `straight_section_friction` / `test_section_span` / `Re=173.736` / `target=26.715`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh` / `straight_section_friction` / `lower_leg` / `Re=121.565` / `target=1.847`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh` / `straight_section_friction` / `test_section_span` / `Re=140.402` / `target=30.668`
- `val_salt_test_2_coarse_mesh_laminar` / `feature_keff` / `corner_upper_right` / `Re=100.760` / `target=11.817`
- `val_salt_test_2_coarse_mesh_laminar` / `feature_keff` / `test_section_complex` / `Re=93.653` / `target=6.209`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` / `feature_keff` / `corner_upper_right` / `Re=59.824` / `target=5.133`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` / `feature_keff` / `corner_upper_right` / `Re=54.689` / `target=4.178`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `feature_keff` / `corner_upper_right` / `Re=90.325` / `target=10.970`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` / `feature_keff` / `test_section_complex` / `Re=84.284` / `target=4.121`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `feature_keff` / `corner_upper_right` / `Re=74.832` / `target=3.760`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `feature_keff` / `test_section_complex` / `Re=69.416` / `target=2.752`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `feature_keff` / `corner_upper_right` / `Re=119.886` / `target=15.398`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` / `feature_keff` / `test_section_complex` / `Re=111.307` / `target=10.205`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh` / `feature_keff` / `corner_upper_right` / `Re=99.012` / `target=13.597`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh` / `feature_keff` / `test_section_complex` / `Re=91.546` / `target=8.859`
- `viscosity_screening_salt_test_4_jin_coarse_mesh` / `feature_keff` / `corner_upper_right` / `Re=162.761` / `target=12.197`
- `viscosity_screening_salt_test_4_jin_coarse_mesh` / `feature_keff` / `test_section_complex` / `Re=150.337` / `target=13.621`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh` / `feature_keff` / `corner_upper_right` / `Re=131.654` / `target=14.476`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh` / `feature_keff` / `test_section_complex` / `Re=121.425` / `target=14.128`

## Exact fit-used thermal rows

- `viscosity_screening_salt_test_2_kirst_coarse_mesh` / `left_lower_leg` / `Re=76.096` / `Nu=3.147`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh` / `left_lower_leg` / `Re=100.420` / `Nu=4.153`

## Sensitivity highlights

- `hydraulic_straight` / `direct_to_shear_gate_loose` / `no` / Loose direct/shear ratio gate 0.40-2.50.
- `hydraulic_straight` / `direct_to_shear_gate_strict` / `yes` / Strict direct/shear ratio gate 0.67-1.50.
- `hydraulic_feature` / `feature_boundary_bin_count_2` / `no` / Feature local-boundary reference rebuilt with 2 nearest finite bins per side instead of 3.
- `hydraulic_feature` / `feature_boundary_bin_count_5` / `no` / Feature local-boundary reference rebuilt with 5 nearest finite bins per side instead of 3.
- `hydraulic` / `late_window_choice` / `unknown` / Hydraulic late-window sensitivity remains unrun because the straight-section defended rows are preserved only as case-level means in the additive dependency package.
- `thermal` / `closure_gate_loose` / `yes` / Thermal closure gate rebuilt with mean residual fraction <= 0.35.
- `thermal` / `closure_gate_strict` / `yes` / Thermal closure gate rebuilt with mean residual fraction <= 0.20.
- `thermal` / `property_convention_case_probe` / `no` / Case-probe property convention uses probe_T_avg_K rather than branch bulk temperature when deriving Re and Nu.
- `thermal` / `late_window_latest_time_only` / `no` / Thermal target rebuilt from the latest retained time only instead of the retained-time case mean.

## Water extension plan

1. repeat the feature local-boundary reference path on the water-family raw case-analysis roots
2. rerun the exact retained-time thermal closure package with water-side `rho*u*cp` property weighting
3. only then build a water-family dependency package with the same defended/screened split used here
