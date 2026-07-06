# Ethan Salt Model Dependency Package v2

Generated: `2026-06-19`

## What changed from v1

This package keeps the defended straight-section friction rows from the June 18
dependency package, adds a new feature-hydraulic hardening path from preserved
patch-`p_rgh` plus local-boundary references, and replaces the earlier mean-based
thermal audit with exact retained-time enthalpy and section-wall-heat closure.

## Counts

- hydraulic fit-used rows: `28`
- feature fit-used rows: `16`
- thermal fit-used rows: `2`

## Recommendation status

- straight-section friction: `provisional_defended`
- feature `K_eff`: `provisional_defended`
- Salt HTC/Nu: `not_defensible_yet`

## Important limitations

- Feature `K_eff` is stronger than the residual-only June 18 path but still uses
  patch-endpoint `p_rgh` with a local straight-reference proxy rather than a full
  feature-path hydro integral.
- Salt Nu remains blocked unless enough direct closure-supported branches survive
  the thermal audit with adequate case diversity.
