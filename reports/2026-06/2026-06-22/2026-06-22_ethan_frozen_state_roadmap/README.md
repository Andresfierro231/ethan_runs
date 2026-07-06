# Ethan Frozen-State Roadmap

Generated: `2026-06-22`

## Purpose

This package freezes the current execution order while the continuation jobs
run and records the board split so non-overlapping agents can proceed without
reopening the same files.

## Phase order

1. Freeze the current retained-time Salt state and report the current closure
   contract.
2. Let the active continuation jobs finish, then refresh the straight-section
   late-window sensitivity package.
3. Keep the new feature-path hydro decomposition and hardening outputs as the
   highest-value blocker reduction already completed in this pass.
4. Rerun the external `Fluid` 1D lane against the frozen-state contract.
5. Only after the 1D replay and continuation refresh, decide whether another
   feature hardening or model-dependency rerun is warranted.

## Boundaries

- Straight sections are not assumed fully developed just because reference
  values exist in the literature.
- `upcomer` remains a separate modeling problem from the direct straight
  branches.
- `right_leg` or downcomer remains blocked for direct Nu until more branchwise
  retained-time observables exist.
- The reopened feature `K_eff` basis is provisional and patch-endpoint based,
  not a continuous field integral.
