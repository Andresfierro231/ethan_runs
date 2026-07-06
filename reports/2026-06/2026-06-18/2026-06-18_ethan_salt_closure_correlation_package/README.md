# Ethan Salt Closure / Correlation Package

Generated: `2026-06-18`

This package is a Salt-only additive closure-first analysis layer built from
the existing June 9, June 15, and June 17 Ethan artifacts. It does not reopen
the active shared extraction or package-builder paths.

## What this package adds

- Salt straight-section hydraulic screening with correlation-fit gates
- Salt feature `K_eff` screening tables
- Salt heat-loss partition indicators from the June 9 audit
- Salt branch thermal usability masks for effective HTC / UA / thermal-resistance use
- Salt legwise enthalpy-balance summary tables
- Salt-only straight-section, feature, and case-level correlation-input tables
- Salt boundary-layer context summaries and the currently available representative Salt landmark profile figure

## Primary interpretation boundaries

1. Straight-section apparent Darcy factors are signed net section closures.
   Negative values are retained as buoyancy-aided or net-gain sections, not
   mislabeled as positive friction losses.
2. Feature `K_eff` still inherits the June 17 residual `p_rgh` feature path;
   this package does not pretend that feature hydro integrals are now fully resolved.
3. Branch thermal fit status is a support mask for effective ratios, not a claim
   that the underlying branch physics are absent when a row is blocked.
4. The heat-loss partition remains case-level and audit-style. It is not yet a
   resolved decomposition into internal convection, wall conduction, and external
   radiation/convection.
5. Representative boundary-layer context is currently limited to the preserved
   Salt 2 landmark profile set already available in the additive June 17 package.

## Main artifacts

- `salt_hydraulic_section_closure.csv`
- `salt_hydraulic_case_summary.csv`
- `salt_feature_keff.csv`
- `salt_heat_loss_partition_case.csv`
- `salt_leg_enthalpy_summary.csv`
- `salt_branch_usability.csv`
- `salt_boundary_layer_summary.csv`
- `salt_representative_boundary_profiles.csv`
- `salt_case_correlation_inputs.csv`
- `salt_straight_section_correlation_inputs.csv`
- `salt_feature_correlation_inputs.csv`
- `salt_fit_exclusion_log.csv`
- `MATH_COMPANION.md`

## Summary counts

- Salt cases covered: `9`
- Straight-section rows: `54`
- Feature rows: `45`
- Branch rows: `63`
- Straight-section fit candidates: `12`
- Branch thermal fit candidates: `36`

## Figures

- hydraulic agreement: `reports/2026-06-18_ethan_salt_closure_correlation_package/figures/png/salt_hydraulic_agreement.png`
- branch usability: `reports/2026-06-18_ethan_salt_closure_correlation_package/figures/png/salt_branch_usability.png`
- heat-loss partition: `reports/2026-06-18_ethan_salt_closure_correlation_package/figures/png/salt_heat_loss_partition.png`
- boundary-layer ratios: `reports/2026-06-18_ethan_salt_closure_correlation_package/figures/png/salt_boundary_layer_ratios.png`
- representative Salt boundary profile: `reports/2026-06-18_ethan_salt_closure_correlation_package/figures/png/salt_representative_boundary_profiles.png`

## Summary JSON

Machine-readable package summary is in `summary.json`.
