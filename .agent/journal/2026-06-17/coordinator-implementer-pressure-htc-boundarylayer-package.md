# AGENT-079 Raw Journal — Pressure / HTC / Boundary-Layer Package

## 2026-06-17

- Read the repo startup instructions, confirmed the active board state, and
  checked the June 15/17 transport ownership before editing anything.
- Confirmed the shared extraction path is actively owned by `AGENT-072`, then
  chose an additive implementation strategy instead of reopening the live
  builder / extractor files.
- Grounded the new package in the existing source-of-truth notes:
  - `reports/2026-06-17_ethan_streamwise_transport_math_reference/README.md`
  - `reports/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md`
  - `reports/2026-06-15_ethan_all_runs_field_transport_campaign/README.md`
- Verified that the June 15 live package roots already contain the raw artifacts
  needed for most of the requested report:
  - `raw_extraction/leg_major_loss_timeseries.csv`
  - `raw_extraction/feature_minor_loss_timeseries.csv`
  - `raw_extraction/feature_patch_pressure_timeseries.csv`
  - `raw_extraction/boundary_layer_landmark_profiles.csv`
  - `raw_extraction/azimuthal_wall_transport_summary.csv`
  - the packaged summary CSVs in each per-case root
- Confirmed an important method boundary before coding:
  - Salt-family bulk temperature is compatible with the requested
    `rho*u*cp` weighting because `Cp_coeffs` are effectively constant.
  - Water-family exact `rho*u*cp` weighting did not initially look recoverable
    from the stored summary CSVs, so the first package draft treated it as a
    report limitation pending a deeper look at the preserved raw surfaces.
- Locked the additive package scope to a fresh builder and report root:
  - `tools/analyze/build_ethan_pressure_htc_boundarylayer_package.py`
  - `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/`
- Decided to use the existing
  `reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_package_index.csv`
  as the canonical case-package index instead of inventing a second case list.
- Implemented the new builder to:
  - load the 13 per-case package roots
  - parse case metadata and fluid-property polynomials from `case_config.yaml`
  - parse gravity from each case `constant/g`
  - compute explicit hydro-corrected straight-section pressure loss from wall
    `p` plus the buoyancy integral
  - cross-check against endpoint and integrated `p_rgh`
  - compute section-local and loop-reference apparent Darcy factors
  - compute core-only shear comparison on straight main-pipe spans
  - reuse the stored feature residual closure to produce `K_eff`
  - compute bulk-vs-centerline temperature corrections
  - compute fluid-side effective `HTC/Nu` field tables from the azimuthal wall
    transport summaries plus the existing bulk-temperature reductions
  - compute legwise and loopwise enthalpy balances
  - compute first-pass boundary-thickness ratios from the landmark summaries
  - write a formal `MATH_COMPANION.md`, main `README.md`, and a machine-readable
    `summary.json`
- Chose to label the boundary-profile figures as
  `sparse_landmark_profile_map` in the representative-map index so the package
  does not overclaim full circumferential boundary-layer coverage.
- Smoke-built the package first for:
  - `val_salt_test_2_coarse_mesh_laminar`
  - `val_water_test_2_coarse_mesh_laminar`
- Found one aggregation defect during the smoke pass:
  - `enthalpy_balance_by_case.csv` was summing every retained time directly,
    which inflated the loop totals
  - fixed by aggregating leg totals per retained time first, then computing
    mean and sum-over-time loop balances separately
- Re-ran the smoke package after the enthalpy fix and verified that the bounded
  output tree contained:
  - the report and math companion
  - section/case pressure closure tables
  - feature `K_eff`
  - effective `HTC/Nu` section summaries
  - enthalpy and boundary-layer summaries
  - representative sparse profile figures
- Promoted the same builder to the durable report root and built all `13` cases.
- Follow-on water-side upgrade after the first durable draft:
  - inspected the preserved June 15 raw extraction roots and confirmed that the
    water-family cases still retain the original cut-plane surface directories
    under `postProcessing/streamwiseBulkThermal/<time>/bulkThermal_*`
  - dynamically loaded the existing major-loss helper module so the additive
    builder could reuse the same face parsing, connected-region detection, and
    support-selection logic without editing the `AGENT-072` extractor files
  - added an additive exact water bulk rebuild that uses:
    - stored per-face `T` and `U` cut-plane samples
    - water `rho(T)` and `cp(T)` polynomials from `case_config.yaml`
    - the requested positive aligned `rho*u_n*cp` weighting
  - kept the old method visible by emitting:
    - `water_bulk_temperature_reweight_comparison.csv`
    - `water_bulk_temperature_reweight_summary.csv`
  - optimized the rebuild after the first slow pass by caching each surface
    geometry and face connectivity across retained times; the expensive step is
    now dominated by rereading the preserved `T` and `U` field files
- Rebuilt the smoke package and then the full durable package after the water
  exact-bulk upgrade.
- Water-bulk comparison results from the final durable package:
  - Water 1 mean exact `rho*u*cp` minus stored bulk: `4.65e-05 K`
  - Water 2 mean exact `rho*u*cp` minus stored bulk: `5.52e-05 K`
  - Water 3 mean exact `rho*u*cp` minus stored bulk: `5.80e-05 K`
  - Water 4 mean exact `rho*u*cp` minus stored bulk: `4.77e-05 K`
  - worst-case absolute exact `rho*u*cp` minus stored bulk across the four
    water cases: `2.27e-04 K`
  - exact `rho*u*cp` minus exact `rho*u` weighting remained tiny as well:
    worst case `8.33e-04 K` on Water 4
- Final durable summary counts:
  - `case_count = 13`
  - `pressure_section_row_count = 78`
  - `feature_row_count = 65`
  - `salt_htc_field_row_count = 218448`
  - `water_htc_field_row_count = 118080`
  - `water_bulk_reweight_row_count = 7580`
  - `enthalpy_leg_row_count = 342`
  - `boundary_ratio_row_count = 1653`
  - `representative_map_count = 12`
- Final durable package size:
  - `174M`
- Important interpretation boundaries preserved in the report:
  - water `HTC/Nu`, enthalpy, and bulk-vs-centerline rows now use the additive
    exact bulk-temperature rebuild instead of the earlier stored June 15 bulk
  - feature `K_eff` is still a `p_rgh` residual closure
  - boundary-layer coverage is still landmark-first rather than a full
    circumferential field reconstruction
