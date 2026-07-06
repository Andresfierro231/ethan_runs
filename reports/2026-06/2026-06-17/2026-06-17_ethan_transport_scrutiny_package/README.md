# Ethan Transport Scrutiny Package

Generated: `2026-06-17T17:27:18-05:00`

This package is the high-scrutiny trust audit for the June 15/17 Ethan
transport workflow. It does not regenerate extraction. It classifies the
existing outputs into `paper_safe`, `internal_only`, and
`do_not_promote` so later paper work can promote only the defensible
subset.

## Canonical Inputs

- package index: `reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_package_index.csv`
- representative Salt 2 package: `reports/2026-06-15_ethan_representative_transport_comparison/summary.json`
- Salt-family campaign: `reports/2026-06-15_ethan_field_transport_campaign/summary.json`
- all-runs campaign: `reports/2026-06-15_ethan_all_runs_field_transport_campaign/summary.json`
- math reference: `reports/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md`
- prior interpretation package: `reports/2026-06-17_ethan_transport_interpretation_package/README.md`

## Scrutiny Rubric

- Effective thermal metrics are `paper_safe` only when usable fraction is
  at least `0.90`, thermal warning fraction is at most `0.10`, and the
  minimum resolved `|T_bulk - T_wall|` is at least `0.50 K`.
- Effective thermal metrics are `do_not_promote` when usable fraction drops
  below `0.75`, the minimum resolved `|T_bulk - T_wall|` falls below
  `0.25 K`, or masked rows dominate too strongly.
- Hydraulic span reductions are `paper_safe` only when the shear-based and
  direct wall-registered reductions agree on pressure-drop direction and
  the direct support fraction stays above `0.75`.
- Boundary-layer landmarks remain `internal_only` context even when present.

## Status Counts By Variable Family

- `boundary_layer_context`: paper_safe=`0`, internal_only=`13`, do_not_promote=`0`
- `direct_pressure_gradient`: paper_safe=`53`, internal_only=`24`, do_not_promote=`1`
- `effective_htc`: paper_safe=`37`, internal_only=`20`, do_not_promote=`34`
- `effective_ua`: paper_safe=`37`, internal_only=`20`, do_not_promote=`34`
- `momentum_resistance`: paper_safe=`53`, internal_only=`24`, do_not_promote=`1`
- `shear_friction`: paper_safe=`53`, internal_only=`23`, do_not_promote=`2`
- `thermal_resistance`: paper_safe=`37`, internal_only=`20`, do_not_promote=`34`

## Highest-Risk Thermal Branches

- `Salt 2 val / right_leg` blocked by `thermal_low_usable_fraction` from `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/val_salt_test_2_coarse_mesh_laminar/branch_thermal_summary.csv`
- `Salt 2 val / upper_leg` blocked by `thermal_small_delta_t` from `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/val_salt_test_2_coarse_mesh_laminar/branch_thermal_summary.csv`
- `Salt 1 Jin / lower_leg` blocked by `thermal_low_usable_fraction` from `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_1_jin_coarse_mesh/branch_thermal_summary.csv`
- `Salt 1 Jin / right_leg` blocked by `thermal_low_usable_fraction` from `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_1_jin_coarse_mesh/branch_thermal_summary.csv`
- `Salt 1 Kirst / lower_leg` blocked by `thermal_low_usable_fraction` from `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_1_kirst_coarse_mesh/branch_thermal_summary.csv`
- `Salt 1 Kirst / right_leg` blocked by `thermal_low_usable_fraction` from `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_1_kirst_coarse_mesh/branch_thermal_summary.csv`
- `Salt 2 Jin / right_leg` blocked by `thermal_low_usable_fraction` from `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_jin_coarse_mesh/branch_thermal_summary.csv`
- `Salt 2 Kirst / right_leg` blocked by `thermal_low_usable_fraction` from `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_kirst_coarse_mesh/branch_thermal_summary.csv`

## Hydraulic Rows That Still Deserve Code-Level Attention

- `Water 1 / left_lower_leg`: `Shear-based and direct wall-registered reductions disagree on the pressure-drop direction.` (tmp/2026-06-15_live_case_analysis/contract_fix_water_family/val_water_test_1_coarse_mesh_laminar/major_loss_summary.csv)
- `Water 2 / left_lower_leg`: `Shear-based and direct wall-registered reductions disagree on the pressure-drop direction.` (tmp/2026-06-15_live_case_analysis/contract_fix_water_family/val_water_test_2_coarse_mesh_laminar/major_loss_summary.csv)

## Paper Promotion Boundary

- Use `paper_safe_asset_map.csv` as the paper-facing gate, not the raw
  campaign directories.
- Any asset marked `allowed_with_caveat` still requires narrow narration
  and explicit acknowledgement of blocked or marginal regions.
- Any asset marked `blocked` should stay out of the main manuscript until
  either the scope narrows to a safe subset or the contradiction is
  resolved upstream.

## Main Artifacts

- `transport_claim_matrix.csv`
- `transport_contradiction_log.csv`
- `paper_safe_asset_map.csv`
- `transport_status_counts.csv`
- `figures/transport_scrutiny_branch_heatmap.*`
- `figures/transport_scrutiny_hydraulic_agreement.*`
- `figures/transport_scrutiny_thermal_qc.*`
