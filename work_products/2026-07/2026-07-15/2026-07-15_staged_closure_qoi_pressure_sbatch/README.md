# Staged Closure-QOI / Raw-Pressure sbatch

Task: AGENT-440
Generated: 2026-07-15

This package stages nominal Salt2/Salt3/Salt4 raw-pressure two-tap
postprocessing onto copied/symlinked scratch cases and submits one compute-node
sbatch job. Native CFD solver outputs remain read-only.

## Current Status

- Preflight rows: `3`
- Preflight failures: `0`
- submitted sbatch script: `scripts/sbatch_staged_closure_qoi_pressure.sh`
- prepared fallback sbatch script: `scripts/submit_staged_closure_qoi_raw_pressure.sbatch`
- submitted job id: `3297845`
- submitted job name: `cqp_stage`
- latest checked state: `COMPLETED`
- harvested rows: `3`
- authoritative parsed harvest: `raw_pressure_two_tap_harvest.csv`

Outputs are diagnostic until admission gates handle pressure definition,
orientation, straight-loss subtraction, mesh/GCI, and recirculation policy.
