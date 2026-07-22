# Pressure-Ladder Unlock Plan And sbatch

Task: AGENT-445
Generated: 2026-07-15

## Why This Exists

AGENT-440 successfully produced two-tap pressure diagnostics, but it did not
unlock final hydraulic residual attribution because two isolated taps cannot
establish pressure orientation, adjacent straight-loss subtraction, branch-local
development behavior, or recirculation masks. This package launches the next
overnight postprocessing step: sample all 30 mesh-centerline station planes for
Salt2/Salt3/Salt4 and harvest station plus adjacent-pair pressure deltas.

## Tomorrow Unlock Plan

1. Check job `3297860` with `sacct`.
2. If terminal, run `python3.11 tools/analyze/build_pressure_ladder_unlock_sbatch.py --harvest --record-job-id 3297860`.
3. Open `station_pressure_ladder.csv` and `adjacent_pressure_ladder.csv`.
4. Build an orientation table by branch using adjacent `p` and `p_rgh` trends.
5. Use branch-specific adjacent pairs to estimate straight/distributed pressure gradients before computing any local/component K.
6. Mask rows with material reverse-area fractions before any true `f_D` or `K` fit.
7. Keep all rows diagnostic until mesh/GCI, pressure definition, tap orientation, straight-loss subtraction, and recirculation gates explicitly admit them.

## Current Status

- Preflight rows: `3`
- Preflight failures: `0`
- Station planes targeted per case: `30`
- Submitted job id: `3297860`
- Latest submitted state: `PENDING_PRIORITY`
- Harvested station row slots: `90`
- Harvested parsed station rows: `90`
- Harvested adjacent row slots: `72`
- Harvested parsed adjacent rows: `72`

## Guardrails

Native CFD outputs are read-only. The sbatch job writes only under
`tmp/2026-07-15_pressure_ladder_unlock_sbatch` and this work-product package. Outputs are diagnostic until an
admission gate promotes them.
