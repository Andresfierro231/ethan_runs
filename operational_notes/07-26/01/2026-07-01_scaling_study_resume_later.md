# Scaling Study — Deferred, Resume Later

Date parked: 2026-07-01
Owner at park: claude (was AGENT-160 handoff)
Decision: **Deferred by user on 2026-07-01.** User wants to focus on the 1D
closure science backlog instead. Do NOT resubmit the scaling jobs until the
user explicitly reopens this lane.

## What happened to the overnight jobs
- `3268028` (rank-count pilot, 32/64/128/256, scotch) — **CANCELLED**, never
  started (`Start=None`, `00:00:00` elapsed, cancelled 2026-07-01T10:29:57). No
  `scaling_summary.csv` produced.
- `3268024` (I/O-policy optimization follow-up) — **CANCELLED** at the same time,
  never started.

Nothing ran; there are no results to analyze. This is a clean re-decision when
the lane reopens.

## How to resume (everything is already staged)
Full context: `.agent/journal/2026-06-30/end-of-day-continuation-handoff.md`
(§AGENT-160) and `.agent/journal/2026-06-30/scaling-study.md`.

- Staging root: `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/`
- Source case (read-only): `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation` (latest retained time `7915`, `nCells:2166996`, 64 ranks / scotch prod).
- Rank pilot script: `scripts/run_salt2_scotch_rank_pilot.sbatch`
- I/O follow-up script: `scripts/run_salt2_method_io_followup.sbatch` (variants:
  scotch_prod_io, scotch_sparse_io, scotch_sparse_compressed, hierarchical_sparse_io)
- To resume: re-submit the rank pilot first; if it favors a non-64 rank, update
  `BENCHMARK_RANKS` in the I/O follow-up before submitting it.

## Why deferred
User priority as of 2026-07-01 is the science backlog (T1/T2/T3 in
`operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`), not runtime
optimization. Optimization has no bearing on paper-facing scientific claims.
