# Thermal Parity Roadmap

Date: 2026-07-10
Task: AGENT-252
Role: Coordinator / Writer

## User Decisions Captured

- Match the CFD boundary contract as closely as feasible, with patch-level
  documentation of what each patch represents.
- Preserve the distinction between realized CFD `wallHeatFlux` for diagnosis
  and imposed CFD inputs for setup documentation.
- Audit whether `rcExternalTemperature` actually uses `emissivity` and `Tsur`;
  use the result to decide whether 1D parity mode includes radiation.
- Target agreement in this order: total heat balance, branch heat loss,
  station/probe temperatures, wall temperatures.
- Prefer a predictive internal thermal-development / wall-adjacent temperature
  model where feasible, with effective internal HTC as a practical diagnostic
  or fallback.
- Build diagnostic mode first, then predictive mode.
- Treat all major sections individually; upcomer, test section, and downcomer
  are expected to be challenging.

## Observed Scheduler State

`sacct -j 3282992,3288671` during this note showed:

- `3282992` Salt1 nominal still running on `c318-016`.
- `3288671` selected corrected-Q job still running on `c318-017`.
- `3288671.0` and `3288671.1` running.
- `3288671.2` failed after about `00:02:33`.

`squeue` was not usable in this sandboxed shell because Slurm socket creation
was blocked. The note therefore uses `sacct` plus AGENT-251's end-of-day state.

## Output

Wrote:

- `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`
- `imports/2026-07-10_thermal_parity_roadmap.json`
- `.agent/status/2026-07-10_AGENT-252.md`

No solver outputs were mutated, no extraction was run, no Fluid code was edited,
and no jobs were submitted.
