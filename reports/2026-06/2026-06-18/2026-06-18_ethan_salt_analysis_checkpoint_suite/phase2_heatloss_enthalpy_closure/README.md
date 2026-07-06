# Phase 2 Heat-Loss / Enthalpy Closure

Generated: `2026-06-18`

This checkpoint focuses on the current Salt heat-loss partition and enthalpy
closure problem.

## Main findings

- Candidate enthalpy rows: `1` of `54`
- Screening enthalpy rows: `1`
- Blocked enthalpy rows: `52`
- Maximum enthalpy residual fraction: `7.788`

## Key outputs

- `heat_partition_case_fractions.csv`
- `leg_enthalpy_closure_screen.csv`
- `enthalpy_case_checkpoint.csv`
- `enthalpy_residual_ranking.csv`

## Interpretation checkpoint

This phase confirms that Salt thermal closure is not yet dissertation-clean.
The current audit-style heat partition is useful for locating where heater
power likely leaves the loop, but the dominant next step is still a more
resolved decomposition that keeps internal convection, wall/insulation
conduction, and external loss channels separate.
