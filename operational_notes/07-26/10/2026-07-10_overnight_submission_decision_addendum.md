# 2026-07-10 Overnight Submission Decision Addendum

## Short Answer

- Harvest/postprocessing: wait for terminal job state; do not launch ungated
  harvest tonight.
- Thermal UA/Nu: not production-submittable yet; repair reconstructed `T` first.
- Time-series uncertainty digest: submittable as a small local analysis/writer
  task, not as an overnight Slurm job.

## Live Jobs To Leave Alone

- `3282992` Salt1 nominal continuation is still running.
- `3288671` selected corrected-Q packed continuation is still partly running.
  Steps `.0` and `.1` are running; step `.2` failed and is repair-first.

## Harvest / Postprocessing Decision

Do not run a normal harvest now. Terminal harvest should wait until a parent job
has actually exited, otherwise the admission memo can be stale.

A dependency-gated `afterany` harvest is technically possible, but not the best
choice tonight because Salt1 may run for days and corrected-Q repair work is
already active under AGENT-253.

Tomorrow or next session:

1. Check `squeue` and `sacct` for `3282992` and `3288671`.
2. Harvest only completed/stopped jobs.
3. Keep Salt1 nominal out of fits until terminal admission passes.
4. Keep corrected-Q rows sensitivity/correlation-support until a formal
   post-continuation gate admits the exact row.

## Thermal UA / Nu Decision

Do not submit a production Thermal UA/Nu extraction tonight.

Current state:

- Pressure-only Salt2 medium/fine extraction works.
- Thermal closure remains blocked by reconstructed-`T` / thermal parsing issues.
- Refined pressure outputs are useful for pressure-only mesh comparison, not for
  thermal UA/HTC/Nu admission.

Next task should be a repair smoke, not a full production run:

1. Diagnose reconstructed `T` for Salt2 medium/fine refined mirrors.
2. Run a minimal thermal sampling smoke.
3. Only after the smoke passes, produce effective `h_eff`, `Nu_eff`, and
   `UA_eff` diagnostics with sign, support, bulk-temperature, recirculation, and
   no-`qr` semantics carried explicitly.

## Time-Series Uncertainty Digest Decision

This is ready and should be done soon. It does not need an overnight job.

Use the AGENT-244 package:

- `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/METHODOLOGY.md`

Recommended deliverable:

- compact Salt2/3/4 admitted-mainline table;
- `osc_mean`;
- `unc_sem_corrected`;
- `osc_rmse_about_trend`;
- drift over 300 s;
- verdict;
- separate handling for near-zero `total_Q` residuals in absolute W.

## Submission Guidance

Submit next only after preconditions:

- terminal harvest/gate after `3282992` exits;
- terminal harvest/gate after surviving `3288671` steps exit;
- Salt4 +10Q repaired attach/resubmit only through AGENT-253 or a successor;
- Thermal UA/Nu only after reconstructed-`T` smoke passes.

No new Slurm submission is recommended from this addendum.
