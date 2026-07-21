# Ethan Frozen-State 1D Validation

Generated: `2026-07-01T16:08:00-05:00`

## Scope

- This package compares the current readable Salt 1D diagnostics against the
  `2026-06-22_ethan_frozen_state_results` CFD contract.
- Primary comparison set: frozen CFD rows labeled `comparison_candidate`.
- Provisional appendix: frozen CFD rows labeled `convergence_audit_required`.
- Straight sections are not assumed fully developed by default.
- `upcomer` remains a separate modeling problem, and `right_leg` / downcomer
  remains blocked for direct internal `Nu`.

## Current closure contract used for interpretation

- Distributed straight friction is read from the local CFD closure bundle term
  `straight_friction_class_aware_re_power_law` on `lower_leg, test_section_span`.
- Primary thermal conductance interpretation is read from
  `primary_ua_profile_library` on `left_lower_leg, test_section_span, left_upper_leg, upcomer`.
- Direct fitted `Nu` remains limited to `left_lower_leg_nu_branch_aware_re_power_law` on
  `left_lower_leg`.
- Best current primary scenario bundle alignment:
  `full_bundle_alignment`.
  Uses the same readable baseline closure stack as the current defended local CFD closure bundle.

## Current best readable picture

- Best full-coverage readable scenario on the primary frozen set: `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` with mean |energy| `11.27%` of heater, mean TW RMSE `62.79 K`, mean TP RMSE `62.69 K`, and mean mass-flow error `26.69%`.
- No hybrid/profile-descriptor rows were readable on the primary comparison set.
- Because the current readable external replay still comes from the June 19
  `ethan_cfd_informed_salt_v1` bundle, these results should be treated as the
  best current local scoring surface rather than a final refreshed-closure
  replay.

## Per-reference winners on the primary set

- Salt 1 Kirst: overall `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, energy `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, TW `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, TP `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, mdot `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`
- Salt 2 Kirst: overall `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, energy `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, TW `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, TP `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, mdot `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`
- Salt 2 Val: overall `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, energy `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, TW `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, TP `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, mdot `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`

## Heat-loss contract used here

- Compare `Q_lost = Q_removed + Q_ambient` on both sides.
- CFD side:
  `cooling_branch_total_removal_w + ambient_proxy_w`.
- 1D side:
  `qhx_total_W + qambient_total_W`.
- Do not infer a hidden cooler `h`, and do not double-count `ambient_proxy_w`.

## Added closure-reference artifacts

- `closure_term_reference.csv`
- `closure_branch_policy.csv`
- `scenario_bundle_alignment.csv`
