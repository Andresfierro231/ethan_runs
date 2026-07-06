# Ethan Salt Model Dependency Package v4

Generated: `2026-06-22`

## What changed from v3

This package keeps the June 19 straight and thermal dependency recommendations
unchanged, but reopens the feature lane using the June 22 defended patch-endpoint
path decomposition.

## Counts

- hydraulic fit-used rows: `12`
- feature fit-used rows: `16`
- thermal fit-used rows: `7`

## Recommendation status

- straight-section friction: `provisional_defended`
- feature `K_eff`: `provisional_defended`
- Salt HTC/Nu: `provisional_defended`

## Important limitations

- Feature `K_eff` is reopened on a defended patch-endpoint path basis, but the
  straight subtraction is still the bounded local-boundary reference rather than
  a continuous field integral through the feature volume.
- Direct Nu remains limited to the surviving left-lower-leg direct domain.
