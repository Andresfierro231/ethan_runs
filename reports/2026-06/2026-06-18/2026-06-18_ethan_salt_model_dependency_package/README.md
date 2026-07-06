# Ethan Salt Model Dependency Package

Generated: `2026-06-18`

## What was run

This package builds the next additive Salt-only analysis layer after the June 18
checkpoint suite. It does **not** reopen the shared June 15/17 extractors.
Instead it audits the preserved Salt closure artifacts and promotes only those
rows that survive explicit closure, support, overlap, and provenance gates.

Primary implementation script:

- `tools/analyze/build_ethan_salt_model_dependency_package.py`

## Inputs used

- `reports/2026-06-18_ethan_salt_analysis_checkpoint_suite/`
- `reports/2026-06-18_ethan_salt_closure_correlation_package/`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/`
- `reports/2026-06-17_ethan_nondimensional_dashboard_package/`
- `reports/2026-06-15_ethan_all_runs_field_transport_campaign/`
- `reports/2026-06-09_ethan_steady_state_heat_flow_audit/`
- `reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`
- source `case_config.yaml` property models at each case source root

## Scientific decision first

The thermal-decomposition pass was implementable from preserved artifacts.
Hydraulic hardening for feature `K_eff` was **not** a prerequisite for that
thermal pass, but the package still writes a hydraulic hardening audit because
feature pressure loss remains residual-only and therefore not fit-defensible.

## Output tables

- `provenance_map.csv`
  Machine-readable lineage map with source files, source columns, formulas,
  units, sign conventions, gates, and known failure modes.
- `thermal_decomposition_rows.csv`
  One late-window branch row per Salt case with bounded decomposition terms,
  closure gates, dimensionless groups, and final fit-use status.
- `thermal_fit_ready_rows.csv`
  Only defended thermal rows promoted into downstream fitting.
- `thermal_exclusion_summary.csv`
  Counted thermal exclusions by primary reason.
- `branch_trust_summary.csv`
  Branch-level counts of screened, closure-supported, fit-used, sensitivity-only,
  and excluded rows.
- `hydraulic_hardening_audit.csv`
  Straight-section and feature hydraulic audit rows with method labels,
  residual-risk flags, and TODO requirements for unfinished feature closure.
- `hydraulic_fit_ready_rows.csv`
  Only defended straight-section hydraulic rows promoted into downstream fitting.
- `hydraulic_exclusion_summary.csv`
  Counted hydraulic exclusions by primary reason.
- `salt_friction_fit_results.json`
  Straight-section friction model results plus the final recommendation status.
- `salt_nu_fit_results.json`
  Thermal HTC/Nu model results plus the final recommendation status.
- `sensitivity_summary.csv`
  Compact sensitivity record showing retained rows, coefficient changes, and
  whether the qualitative conclusion changes.
- `model_dependency_handoff.md`
  Future-model-builder handoff with exact row subsets, assumptions, uncertainty,
  and extension plan.

## Fit-ready row counts before and after

- Thermal screened candidates before closure hardening: `36`
- Thermal defended fit-used rows after closure hardening: `1`
- Hydraulic screened straight-section candidates before hydraulic hardening audit: `12`
- Hydraulic defended fit-used rows after hydraulic hardening audit: `12`

## What was excluded and why

### Thermal

- `thermal_branch` / `derived_branch_overlap_double_counting`: `9` rows
- `thermal_branch` / `enthalpy_wall_heat_balance_loose`: `26` rows
- `thermal_branch` / `right_leg_blocked_by_policy`: `9` rows
- `thermal_branch` / `thermal_low_usable_fraction`: `2` rows
- `thermal_branch` / `thermal_small_delta_t`: `2` rows
- `thermal_branch` / `thermal_support_marginal`: `14` rows

### Hydraulic

- `feature_keff` / `feature_pressure_method_residual_only`: `19` rows
- `feature_keff` / `nonpositive_residual_feature_loss`: `26` rows
- `straight_section_friction` / `buoyancy_aided_or_net_gain_section`: `18` rows
- `straight_section_friction` / `direct_to_shear_magnitude_gap`: `13` rows
- `straight_section_friction` / `support_fraction_below_floor`: `11` rows

## Dependency status

### Salt friction dependency

- Recommendation status: `provisional_defended`
- Recommended model: `class_aware_re_power_law`
- Feature `K_eff` status: `not defensible yet` until a feature-path hydro
  integral or equivalent direct feature closure is preserved upstream.

### Salt HTC/Nu dependency

- Recommendation status: `not_defensible_yet`
- Recommended model: `exploratory_screened_only_model`
- Important boundary: right-leg rows stay excluded and derived `upcomer` rows
  remain sensitivity-only because they overlap the direct component spans.

## Reproduction

Run:

```bash
python tools/analyze/build_ethan_salt_model_dependency_package.py --output-dir reports/2026-06-18_ethan_salt_model_dependency_package
```

For a bounded smoke rebuild:

```bash
python tools/analyze/build_ethan_salt_model_dependency_package.py \
  --output-dir /scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/2026-06-18_ethan_salt_model_dependency_package_smoke \
  --source-id val_salt_test_2_coarse_mesh_laminar \
  --source-id viscosity_screening_salt_test_4_jin_coarse_mesh
```

## Known limitations

- The package separates intended-transfer versus parasitic-loss wall exchange
  only to the extent the preserved thermal-role metadata supports it. It does
  **not** claim a resolved wall-conduction / external-convection / radiation
  resistance split.
- Feature `K_eff` still inherits a residual-only `p_rgh` method and therefore
  stays out of defended fitting.
- Hydraulic late-window sensitivity could not be rerun from preserved artifacts
  because only time-mean hydro-corrected section closures survived in the
  additive package.
- If thermal defended rows remain sparse, the package will report that no
  defended Salt Nu dependency is available rather than silently fitting the
  screened-only subset.

## Next recommended work

1. Add an upstream feature-path hydro-integral extractor so feature `K_eff`
   can be promoted out of the residual-only bucket.
2. Preserve a resolved wall-resistance split if future CFD postprocessing needs
   true internal-HTC closure rather than bounded effective Nu.
3. Only after the same closure gates exist for water should the same dependency
   package be extended to water-family rows.
