# Salt-Family Field Transport Campaign

## Scope

This package compares per-case field-transport outputs that publish streamwise heat-loss and azimuthal wall-transport reductions.

Included packages:
- `val_salt_test_2_coarse_mesh_laminar` from `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-15_live_case_analysis/contract_fix_salt2/val_salt_test_2_coarse_mesh_laminar`
- `viscosity_screening_salt_test_1_jin_coarse_mesh` from `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_1_jin_coarse_mesh`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh` from `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_1_kirst_coarse_mesh`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` from `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_jin_coarse_mesh`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` from `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_kirst_coarse_mesh`
- `viscosity_screening_salt_test_3_jin_coarse_mesh` from `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_3_jin_coarse_mesh`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh` from `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_3_kirst_coarse_mesh`
- `viscosity_screening_salt_test_4_jin_coarse_mesh` from `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_4_jin_coarse_mesh`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh` from `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_4_kirst_coarse_mesh`

## Method

- `streamwise_heat_loss_summary.csv` provides total signed and absolute loopwise heat-loss reductions.
- `parasitic_heat_loss_summary.csv` groups those reductions by the case-profile thermal role groups, currently `intended_transfer` and `parasitic_loss` for the Salt-family path.
- `azimuthal_transport_mean_summary.csv` is collapsed to circumferential means using exported wall-face area weights so cross-case friction and wall-heat comparisons stay tied to the sampled wall geometry.
- `branch_thermal_summary.csv` carries branch-local bulk temperature, mass-flux support, and support-gated effective thermal reductions for the six repaired span sections plus the derived `upcomer` branch when the input packages were rebuilt on the June 17 branch-thermal path.
- The same branch summary rows now carry thermal-support QC metrics such as usable fraction, positive mass-flux support, and minimum resolved `|T_bulk - T_wall|`, so branch comparisons can distinguish physical trends from support-limited bins.

## Assumptions And Limits

- This builder assumes every input package is already QC-clean enough to advertise both azimuthal and streamwise heat-loss outputs. It does not repair partial packages.
- Grouped parasitic-vs-intended results depend on `tools/case_analysis_profiles.py` thermal role metadata. Reclassifying a patch family changes the interpretation of these aggregates.
- Branch thermal means reuse the per-case support-gated thermal rows. Masked thermal rows remain excluded from branch HTC / UA' / R_th means, so sparse support can still matter when comparing cases.
- Boundary-layer landmarks are intentionally not re-reduced here; use the representative Salt 2 package or the per-case package roots when near-wall landmark context matters.

## Artifacts

- `field_transport_package_index.csv`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_field_transport_campaign/field_transport_package_index.csv`
- `field_transport_streamwise_heat_comparison.csv`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_field_transport_campaign/field_transport_streamwise_heat_comparison.csv`
- `field_transport_grouped_heat_comparison.csv`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_field_transport_campaign/field_transport_grouped_heat_comparison.csv`
- `field_transport_azimuthal_transport_comparison.csv`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_field_transport_campaign/field_transport_azimuthal_transport_comparison.csv`
- `field_transport_branch_thermal_comparison.csv`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_field_transport_campaign/field_transport_branch_thermal_comparison.csv`
- `figures/`: cross-case heat-loss, circumferential-mean azimuthal transport, branch-thermal comparisons, and branch-thermal QC comparisons
