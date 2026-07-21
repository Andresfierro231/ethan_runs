# 1D Setup And Confidence

Generated: `2026-06-26T10:39:11-05:00`

## Comparison basis

- This bakeoff compares the 1D model against CFD-derived frozen-state results, not against experimental temperatures or experimental mass flow.
- The primary CFD truth basis is `late_window_mean` from `reports/2026-06-22_ethan_frozen_state_results/frozen_state_contract.csv`.
- Experimental values still exist inside the external `Fluid` reporting roots for provenance, but the local frozen-state validation surfaces in this package are CFD-to-1D.

## Active 1D model used here

- Active solver lineage: `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2`
- Active mode: `predictive_airside_hx`
- Legacy second model still in the repo: the older `first_order_model_tamu_loop.py` style path, retained only as historical lineage.
- This bakeoff is using the current `tamu_loop_model_v2` path, not the legacy solver.

## Scenario actually scored here

- Defended full-coverage scenario: `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`
- Defended winner setup class: `baseline` with base `insulation_thickness_in = 1.0 in` and `radiation_on = true`.
- The defended winner is the baseline member, so it does not apply the hybrid branchwise outer-loss multipliers.
- The broader readable `ethan_cfd_informed_salt_v1` family only publishes base `1.0 in` and `2.0 in` conditions, but its hybrid rows can still apply branchwise effective insulation multipliers:
  `heated_incline=0.85x`, `left_lower_vertical=0.90x`, `test_section=0.95x`,
  `left_upper_vertical=0.90x`, `right_vertical=1.40x`,
  `cooled_incline_pre_hx=1.50x`, `cooled_incline_post_hx=1.50x`.
- Therefore the current defended result is not already a global `1.4 in` case.
  If the representative CFD physical setup should be treated as globally
  `1.4 in`, the present defended winner is a setup-mismatched surrogate rather
  than a final physically matched predictive result.

## Branch closure assignment

- Distributed straight friction:
  `straight_friction_class_aware_re_power_law`
  on `lower_leg|test_section_span`, status `provisional_defended`
- Direct internal thermal law:
  `left_lower_leg_nu_branch_aware_re_power_law`
  on `left_lower_leg` only, status `provisional_defended_limited_domain`
- Primary thermal closure:
  `primary_ua_profile_library`
  on `left_lower_leg|test_section_span|left_upper_leg|upcomer`
- Secondary thermal diagnostic surface:
  `secondary_htc_profile_library`
  on `left_lower_leg|test_section_span|left_upper_leg|upcomer`
- Unsupported or blocked branches:
  `right_leg` / downcomer, cooler return, and feature losses remain on residual or calibration-only lanes
- Defended winner bundle alignment:
  `full_bundle_alignment`.
  Uses the same readable baseline closure stack as the current defended local CFD closure bundle.

## Insulation and radiation treatment

- Insulation is represented as an effective radial resistance on insulated segments.
- The active scenario sets fixed `insulation_thickness_in` and may also apply per-parent effective insulation multipliers.
- In the defended winner, the insulation treatment is uniform at the base thickness with no hybrid branchwise multipliers.
- External convection is modeled with a blended Churchill-Chu natural-convection correlation.
- Radiation is modeled as linearized Stefan-Boltzmann exchange to ambient.
- Radiation is active only when `radiation_on = true`.
- Non-test-section emissivity follows the insulation material default; the test section uses quartz emissivity `0.95`.

## Heat-source and sink treatment

- Salt cases use tracked heater power plus a separate `37 W` quartz test-section source in the current `Fluid/configs/cases.yaml` contract.
- The active predictive mode solves the cooling-jacket duty from the air-side boundary condition.
- The frozen-CFD comparison closes heat loss with `Q_lost = Q_removed + Q_ambient`, where `Q_ambient` is the CFD-side `ambient_proxy_w` bookkeeping quantity.

## Confidence and uncertainty

- Highest confidence:
  CFD late-window heat ledger, left-lower-leg direct developing-flow thermal evidence, and the existence of strong branch-to-branch development differences.
- Medium confidence:
  full-coverage baseline winner on the current frozen surface, as a CFD-matched
  scoring result within the currently published external scenario menu.
- Lower confidence:
  hybrid/profile-descriptor ranking beyond Salt 1, because the readable external `v1` bundle still lacks domain breadth.
- Explicitly uncertain:
  physically matched insulation if the intended CFD setup is `1.4 in`, direct downcomer HTC, and any one-law treatment of the whole upcomer branch.
