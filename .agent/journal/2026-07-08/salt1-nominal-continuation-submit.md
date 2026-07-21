# Salt 1 Nominal Continuation Submit

Date: `2026-07-08`
Task: `AGENT-206`
Role: Coordinator / Implementer / Writer

## Summary

Staged and submitted a corrected Salt 1 nominal continuation job from the June
25 `salt1_jin_basecont` candidate.

The original staged Salt 1 continuation was not corrected for a new long run:
its convergence monitor still called `stopAt(writeNow)`. The new staged copy
changes that monitor to diagnostic-only and starts from the June 25 source
tree's `4026.15625 s` retained `processors64` state.

## Artifacts

- Campaign:
  `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate`
- Launcher:
  `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/scripts/run_salt1_nominal_continuation.sbatch`
- Manifest:
  `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/manifest.csv`
- Submission table:
  `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/submitted_jobs.csv`
- Operational note:
  `operational_notes/07-26/08/2026-07-08_salt1_nominal_continuation_submit.md`

## Submission

Direct `sbatch` from this shell returned:

`NOTIFICATION: sbatch not available on compute nodes. Use a login node.`

Submitted through `login3.ls6.tacc.utexas.edu`:

```bash
sbatch -t 120:00:00 -J salt1_nom_cont --export=ALL jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/scripts/run_salt1_nominal_continuation.sbatch
```

Result: `Submitted batch job 3282992`.

Queue check: `3282992|salt1_nom_cont|PENDING|0:00|5-00:00:00|1|(Priority)`.

## Caveat

This is a single 64-rank job. It cannot be packed with later-identified cases
after launch; those should be submitted separately or grouped in a new packed
allocation.
