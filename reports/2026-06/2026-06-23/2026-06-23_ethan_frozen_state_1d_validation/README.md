# Ethan Frozen-State 1D Validation

Generated: `2026-06-23T10:56:59-05:00`

## Scope

- This package compares the current readable Salt 1D diagnostics against the
  June 22 frozen-state CFD contract.
- Primary comparison set: frozen CFD rows labeled `comparison_candidate`.
- Provisional appendix: frozen CFD rows labeled `convergence_audit_required`.
- Straight sections are not assumed fully developed by default.
- `upcomer` remains a separate modeling problem, and `right_leg` / downcomer
  remains blocked for direct internal `Nu`.

## Current best readable picture

- Best full-coverage readable scenario on the primary frozen set: `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1` with mean |energy| `11.27%` of heater, mean TW RMSE `62.79 K`, mean TP RMSE `62.69 K`, and mean mass-flow error `26.69%`.
- Hybrid/profile-descriptor scenarios reached only `3` primary comparison rows, so they remain under-covered relative to the baseline family.
- Because the current readable external replay still comes from the June 19
  `ethan_cfd_informed_salt_v1` bundle, these results should be treated as the
  best current local scoring surface rather than a final refreshed-closure
  replay.

## Per-reference winners on the primary set

- Salt 1 Kirst: overall `ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_1`, energy `ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_0`, TW `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, TP `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, mdot `ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_1`
- Salt 2 Kirst: overall `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, energy `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_0`, TW `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, TP `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, mdot `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`
- Salt 2 Val: overall `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, energy `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_0`, TW `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, TP `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`, mdot `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`

## Heat-loss contract used here

- Compare `Q_lost = Q_removed + Q_ambient` on both sides.
- CFD side:
  `cooling_branch_total_removal_w + ambient_proxy_w`.
- 1D side:
  `qhx_total_W + qambient_total_W`.
- Do not infer a hidden cooler `h`, and do not double-count `ambient_proxy_w`.
