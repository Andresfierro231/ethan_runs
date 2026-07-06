# AGENT-111 Journal

Date: `2026-06-23`

## Intent

Implement the local frozen-CFD-vs-readable-1D validation lane described in the
June 23 execution plan. This pass stays inside repo-local analysis and report
paths, reuses the June 22 frozen-state and heat-balance contracts, and avoids
the active external `Fluid/**` refresh lane.

## Working Boundaries

- Use `comparison_candidate` rows as the primary presentation-safe set.
- Keep `convergence_audit_required` rows separate as provisional context.
- Treat straights as developing; do not assume fully developed by default.
- Keep `upcomer` separate from direct straight-branch internal-HTC claims.
- Use the documented Salt heat-balance contract:
  `Q_in - Q_lost = 0`, with `Q_lost = Q_removed + Q_ambient`.

## Results

- New local package:
  `reports/2026-06-23_ethan_frozen_state_1d_validation/`
- Primary frozen reference count: `3`
  - `Salt 1 Kirst`
  - `Salt 2 Kirst`
  - `Salt 2 Val`
- Best full-coverage readable scenario on that primary set:
  `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`
- Mean primary-set errors for that row:
  - energy-loss mismatch: `11.27%` of heater
  - wall-temperature RMSE: `62.79 K`
  - centerline-temperature RMSE: `62.69 K`
  - mass-flow error: `26.69%`
- Salt 1 is the only primary frozen case where a hybrid/profile-descriptor row
  wins overall, and even there the temperature miss remains large.
- Salt 2 still prefers the baseline `1.0 in` / radiation-on readable row over
  the currently readable alternatives.

## Interpretation

- The current readable June 19 `Fluid` surface is not merely stale in
  provenance; it is also quantitatively far from the frozen CFD pseudo-steady
  references on TP/TW and mass flow.
- The worst current mismatches cluster at loop-start / upper-side probes:
  `TP3`, `TP4`, `TP5`, `TW9`, `TW10`, and `TW6`.
- That miss pattern is consistent with the current branch authority:
  `left_lower_leg` is still the best direct thermal-evidence lane, while the
  upper-side/upcomer/right-side branches still require different closure
  handling or an externally refreshed 1D bundle.

## Remaining Blocker

- `AGENT-102` still owns the external `Fluid/**` refresh lane.
- The next necessary step is to regenerate the versioned external Salt bundle
  and rerun the same scorecard on that refreshed 1D surface.
