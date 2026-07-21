# TODO

- After the overnight job exits, inspect `results/scaling_summary.csv`.
- Parse each rank log for stable timestep count, solver-iteration counts,
  final `ExecutionTime`, and final `ClockTime`.
- Decide whether `32`, `64`, `128`, or `256` ranks is the best candidate by
  walltime and by core-hours.
- If clean, schedule the next overnight comparison: `scotch` versus
  geometry-aligned `hierarchical`.
- Before the 2026-07-01 20:00 CDT follow-up starts, optionally update
  `BENCHMARK_RANKS` in the submitted job environment/script if the first
  rank-count pilot strongly favors a rank count other than `64`.
