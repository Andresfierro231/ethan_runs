# Ethan 1D Closure Bakeoff

Generated: `2026-06-26T10:39:11-05:00`

## Scope

- This package stages a local shadow bakeoff from the `2026-06-22_ethan_frozen_state_results` Salt contract.
- It does not invent a new `Fluid` rerun. The only readable external diagnostics on disk remain the June 19 `ethan_cfd_informed_salt_v1` bundle.
- Two surfaces are published:
  - `baseline_full_surface`: all readable Salt status rows copied into a local shadow table
  - `defended_full_coverage_surface`: the single full-coverage scenario that kept every Salt case accepted and valid in the shadow table

## Current closure contract used for interpretation

- Distributed straight friction is read from the local CFD closure bundle term
  `straight_friction_class_aware_re_power_law` on `lower_leg, test_section_span`.
- Primary thermal conductance interpretation is read from
  `primary_ua_profile_library` on `left_lower_leg, test_section_span, left_upper_leg, upcomer`.
- Direct fitted `Nu` remains limited to `left_lower_leg_nu_branch_aware_re_power_law` on
  `left_lower_leg`.
- Defended winner bundle alignment:
  `full_bundle_alignment`.
  Uses the same readable baseline closure stack as the current defended local CFD closure bundle.

## Current defended result

- Shadow baseline rows: `15` across `6` scenarios.
- Defended full-coverage scenario: `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` with `4/4` accepted Salt rows.
- Baseline surface best primary scenario: `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` with mean |energy| `11.27%` heater and mean mass-flow error vs CFD `26.69%`.
- Defended surface primary scenario: `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` with mean |energy| `11.27%` heater and mean mass-flow error vs CFD `26.69%`.

## Interpretation boundary

- This is a scoring and filtering bakeoff, not a refreshed 1D physics bundle.
- The defended subset is useful because it removes under-covered hybrid rows and keeps one scenario family that stayed readable across Salt 1-4.
- A real closure retune still requires a new external diagnostics bundle; this package only makes the current local modeling boundary explicit.
- The added dated validation table and heater-partition table in this package are CFD-last-window tables, not experiment tables.
- The defended winner is the baseline `1.0 in` radiation-on member, not the hybrid branch-adjusted member.
- The currently scored readable external bundle only publishes base `1.0 in` / `2.0 in` conditions. Hybrid rows can apply branchwise effective insulation multipliers, including `right_vertical = 1.40x`, but no readable global `1.4 in` Salt scenario is published yet.
- If the target CFD insulation is globally `1.4 in`, treat the present winner as a bounded surrogate until that condition is rerun or explicitly published.
- The top-level bakeoff directory already contained extra `11:29` artifacts before this pass completed. They were preserved in place; the new driver guarantees only the shadow status CSVs, `surface_summary.csv`, `summary.json`, `README.md`, and the two rebuilt surface subdirectories.

## Added closure-reference artifacts

- `closure_term_reference.csv`
- `closure_branch_policy.csv`
- `scenario_bundle_alignment.csv`
