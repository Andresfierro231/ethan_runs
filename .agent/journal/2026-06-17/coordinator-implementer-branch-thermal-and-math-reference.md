# AGENT-072 Raw Journal — Branch Thermal And Math Reference

## 2026-06-17

- Reopened the June 17 TODO and confirmed the current package already computes
  per-bin matched bulk temperature, wall temperature, wall heat flux, effective
  HTC, effective `UA'`, thermal resistance, shear-based friction, direct
  wall-registered pressure gradients, and momentum-resistance proxies inside
  `tools/extract/sample_leg_centerline_major_loss.py`.
- Confirmed the per-case package builder was the right implementation surface
  for the new branch request because `major_loss_cumulative_timeseries.csv`
  already carries the needed thermal-support and bulk-state fields.
- Locked the branch request to:
  - keep the six current repaired span sections as first-class outputs
  - add one derived branch `upcomer = left_lower_leg + test_section_span + left_upper_leg`
  - skip corners and junctions in the derived branch coordinate
  - use flow-weighted branch summaries
- Added `derived_thermal_branches` to `CaseAnalysisProfile` so branch metadata
  lives in the shared profile definition instead of being hardcoded inside the
  package builder.
- Implemented branch-thermal package assembly in
  `tools/analyze/build_ethan_case_analysis_package.py`:
  - `branch_thermal_profiles.csv`
  - `branch_thermal_summary.csv`
  - new branch thermal figures
  - dedicated `upcomer` concatenated detail figure
  - new `summary.json` section and README language
- Chose to keep extraction unchanged. The new branch layer is derived from
  already-vetted major-span cumulative rows so the raw extraction contract does
  not branch or duplicate logic.
- First smoke rebuild failed because `summarize_major_rows()` did not preserve
  `mdot_mean_abs_kg_s` in `cumulative_rows`, which the branch-summary layer
  needs for branch bulk-flow reporting. Fixed by carrying
  `mdot_mean_abs_kg_s` into the cumulative-row payload.
- Raw-reuse smoke rebuild then succeeded for:
  - `tmp/2026-06-17_branch_thermal_smoke/viscosity_screening_salt_test_2_jin_coarse_mesh`
- Smoke checks confirmed:
  - `branch_thermal.available = true`
  - branch order:
    - `lower_leg`
    - `right_leg`
    - `left_lower_leg`
    - `test_section_span`
    - `left_upper_leg`
    - `upper_leg`
    - `upcomer`
  - summary rows = `7`
  - new branch figure paths exist in `summary.json`
- Promoted the same raw-reuse rebuild into the actual Salt 2 package roots:
  - `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_jin_coarse_mesh`
  - `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_kirst_coarse_mesh`
  - `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/val_salt_test_2_coarse_mesh_laminar`
- Verified all three real Salt 2 package roots now report:
  - `branch_thermal.available = true`
  - branch order `lower_leg, right_leg, left_lower_leg, test_section_span, left_upper_leg, upper_leg, upcomer`
- Wrote the new rigorous methods package at
  `reports/2026-06-17_ethan_streamwise_transport_math_reference/`
  instead of patching the June 10 Salt 2 note in place. This keeps the older
  package historically intact while creating one current source-of-truth note
  for the June 15/17-era variables.
- Extended `tools/analyze/build_ethan_field_transport_campaign.py` so the
  Salt-family campaign now also requires and republishes
  `branch_thermal_summary.csv`.
- Added:
  - `field_transport_branch_thermal_comparison.csv`
  - `field_transport_branch_thermal_comparison.{png,svg,pdf}`
  to `reports/2026-06-15_ethan_field_transport_campaign/`.
- Raw-reuse rebuilt the remaining six Salt-family package roots under
  `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/` so all nine
  Salt-family packages now advertise `branch_thermal.available = true` with
  branch count `7`.
- Rebuilt the Salt-family campaign package and verified:
  - `summary.json.artifacts.branch_thermal_csv`
  - `summary.json.figure_paths.branch_thermal_comparison`
  - package count still `9`
- Operational caveat: the all-runs campaign builder now expects
  `branch_thermal_summary.csv` from every input package. The pending or future
  water-family package builds therefore need to finish on the updated builder
  path before the all-Ethan field-transport campaign is treated as current.
- Reopened the already-finished water package roots under
  `tmp/2026-06-15_live_case_analysis/contract_fix_water_family/` and confirmed
  they still predated the branch schema: `boundary_layer` and `azimuthal`
  existed, but `branch_thermal` was absent.
- Raw-reuse rebuilt all four water package roots on the updated builder path:
  - `val_water_test_1_coarse_mesh_laminar`
  - `val_water_test_2_coarse_mesh_laminar`
  - `val_water_test_3_coarse_mesh_laminar`
  - `val_water_test_4_coarse_mesh_laminar`
- Verified all four water package roots now report:
  - `branch_thermal.available = true`
  - the same branch order as the Salt-family packages
  - nonzero usable/masked row counts in the new branch summary section
- Rebuilt `reports/2026-06-15_ethan_all_runs_field_transport_campaign/` on the
  full updated 13-package set.
- Verified the all-runs campaign now publishes:
  - `field_transport_branch_thermal_comparison.csv`
  - `field_transport_branch_thermal_comparison.{png,svg,pdf}`
  - `summary.json.artifacts.branch_thermal_csv`
  - `summary.json.figure_paths.branch_thermal_comparison`
  - `package_count = 13`
- Added a new per-case thermal-support QC reduction layer to
  `tools/analyze/build_ethan_case_analysis_package.py`:
  - `thermal_support_qc_summary.csv`
  - `figure_paths.thermal_support_summary`
  - new branch summary fields for minimum resolved `|T_bulk - T_wall|`,
    positive mass-flux support, area-ratio support, and status breakdown
- Verified the new QC artifacts on a Salt 2 Jin smoke rebuild, then promoted
  the same schema into all 13 real per-case package roots with raw-reuse
  rebuilds.
- Extended `tools/analyze/build_ethan_representative_transport_comparison.py`
  so the representative Salt 2 package now also publishes:
  - `representative_branch_thermal_summary.csv`
  - `summary.json.figure_paths.branch_thermal_summary`
- Extended `tools/analyze/build_ethan_field_transport_campaign.py` so both the
  Salt-family and all-Ethan campaigns now also publish:
  - `figure_paths.branch_thermal_qc_comparison`
  using the rebuilt branch summary rows as the QC source.
- Added the internal evidence-first interpretation package at
  `reports/2026-06-17_ethan_transport_interpretation_package/`, grounded in
  the current representative and campaign CSVs rather than in older monitor-only
  outputs.
- Reopened the transport follow-on work as a scrutiny gate rather than another
  extraction pass. Confirmed the necessary trust signals already existed in the
  rebuilt per-case packages:
  - `major_loss_summary.csv`
  - `branch_thermal_summary.csv`
  - `thermal_support_qc_summary.csv`
  together with the representative and campaign package summaries.
- Added `tools/analyze/build_ethan_transport_scrutiny_package.py` so the
  transport trust audit is reproducible and not trapped in prose. The builder:
  - reads the current 13-package index from the all-runs campaign by default
  - classifies hydraulic span rows into `paper_safe`, `internal_only`, or
    `do_not_promote` based on shear-vs-direct sign agreement and direct support
  - classifies branch thermal rows on explicit QC thresholds for usable
    fraction, warning fraction, and minimum `|T_bulk - T_wall|`
  - blocks boundary-layer outputs from headline use by default
  - writes a machine-readable paper promotion gate
- First smoke run failed because the raw branch rows use `branch_name`, not the
  claim-matrix `scope_name`, inside the thermal-QC plot helper.
- Second smoke run failed because the local Python `zip()` implementation does
  not accept the `strict=` keyword; removed that assumption to keep the builder
  portable on the current machine.
- Third smoke pass exposed the real schema nuance: per-case
  `branch_thermal_summary.csv` does not carry a literal `usable_fraction`
  column even though the campaign summaries do. Fixed the loader to derive
  `usable_fraction = usable_row_count / total_row_count` when the explicit
  column is absent.
- Smoke rebuild then succeeded at:
  - `tmp/2026-06-17_ethan_transport_scrutiny_package_smoke/`
- Promoted the same run into the durable report package:
  - `reports/2026-06-17_ethan_transport_scrutiny_package/`
- The durable scrutiny package now publishes:
  - `transport_claim_matrix.csv`
  - `transport_contradiction_log.csv`
  - `paper_safe_asset_map.csv`
  - `transport_status_counts.csv`
  - three figure families for branch trust, hydraulic agreement, and thermal QC
- Current scrutiny results from the generated package:
  - branch thermal rows:
    - `37` paper-safe
    - `20` internal-only
    - `34` do-not-promote
  - current Salt-paper-safe branch subset:
    - `left_lower_leg`
    - `test_section_span`
    - `left_upper_leg`
    - `upcomer`
  - current code-fix contradiction count:
    - `2`
    - both on water-family `left_lower_leg`
- Added the provenance manifest at:
  - `imports/2026-06-17_ethan_transport_scrutiny_package.json`
- Updated the June 17 TODO so the next actions are now explicit:
  - open a separate `../papers` task before any new `3d_analysis` promotion
  - use `paper_safe_asset_map.csv` as the promotion gate
  - investigate the two water `left_lower_leg` hydraulic contradiction rows
