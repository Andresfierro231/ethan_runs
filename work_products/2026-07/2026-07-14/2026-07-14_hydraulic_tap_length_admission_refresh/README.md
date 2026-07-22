# Hydraulic Tap-Length Admission Refresh

Date: 2026-07-14

## Decision

This package implements the HYD-TAP slice from the hydraulic plan. Existing mesh-centerline station artifacts replace the `abs(dz)` tap-length proxy for preserved corner rows where endpoint stations are available. This is a diagnostic/admission refresh only: it does not mutate CFD outputs, edit external Fluid code, fit thermal terms, or introduce a global hydraulic multiplier.

## Result

- Rows with centerline length resolved: 12
- Rows still missing centerline/raw two-tap evidence: 3
- Component/cluster K rows recomputed: 15
- Fit-admissible component/cluster K rows: 0
- Rows still blocked by mesh/GCI after tap refresh: 6
- Recirculation diagnostic rows: 6

## Recommended Next Work

1. Use this package as the H1 local-K evidence refresh, but do not fit component/cluster K yet because no row is fit-admissible.
2. Run raw two-tap extraction for `test_section_complex` rows if those connector losses are still needed.
3. Move to the Fluid reset/development API row next; H1 remains blocked until reset/development terms and admitted pressure evidence are first-class.
