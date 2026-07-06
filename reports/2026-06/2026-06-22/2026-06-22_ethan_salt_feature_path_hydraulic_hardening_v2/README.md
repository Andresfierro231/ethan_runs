# Ethan Salt Feature-Path Hydraulic Hardening v2

Generated: `2026-06-22`

## What changed

This refresh replaces the earlier v3 blocker-only status with the new June 22
pathwise decomposition:

- exact patch-endpoint `p` and `p_rgh` differences are now explicit
- the local straight subtraction remains the same bounded boundary-reference
  method
- rows with positive retained-time feature excess and complete support are
  allowed back into the feature hardening lane

## Counts

- feature case rows: `45`
- fit-ready feature case rows: `21`

## Important boundary

The feature signal is now defended as a patch-endpoint path decomposition with
the existing local straight reference. It is still not a continuous field
integral through the feature volume, so downstream claims should remain
`provisional_defended` rather than stronger than that.
