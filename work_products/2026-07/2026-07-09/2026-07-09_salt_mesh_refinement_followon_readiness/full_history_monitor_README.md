# Salt Mesh Full-History Monitor Reduction

Generated: `2026-07-09T10:42:32-05:00`

This package merges existing postProcessing restart segments for Salt 2/4 Jin
coarse, medium, and fine mesh endpoint cases. It is read-only and does not run
OpenFOAM utilities.

## Outputs

- `endpoint_full_history_monitor_summary.csv`: scalar monitor statistics from
  merged restart histories.
- `endpoint_postprocessing_family_coverage.csv`: per-family segment/file
  coverage, including velocity-profile snapshot coverage.
- `full_history_monitor_summary.json`: counts and provenance.

## Interpretation Boundary

Rows with `series_verdict=stationary` or `quasi_stationary` are reasonable
screening evidence for mesh-UQ readiness. Rows marked `drifting_or_oscillatory`,
`short_or_partial`, or `missing_monitor` must not be promoted to GCI input
without a later admission decision.
