# Overnight Submission Decision Addendum

Date: `2026-07-10`
Task: `AGENT-255`
Role: Coordinator / Writer

## Prompt

The user asked what still needs to be documented, whether log/postprocessing
harvests should be launched overnight, whether the Thermal UA path is
submittable, and whether the time-series uncertainty digest is submittable.

## Observed Live State

Commands checked:

```bash
squeue -j 3282992,3288671 -o '%i|%j|%T|%M|%l|%D|%R'
sacct -j 3282992,3288671 --format=JobID,JobName%32,State,ExitCode,Elapsed,Start,End,Timelimit,NodeList%20 -P
```

Observed:

- `3282992` / `salt1_nom_cont`: `RUNNING`, elapsed about `2-04:08`.
- `3288671` / `saltq_sel_cont`: `RUNNING`, elapsed about `5:10`.
- `3288671.0` and `3288671.1`: `RUNNING`.
- `3288671.2`: `FAILED` after `00:02:33`.

The board also shows `AGENT-253` active on corrected-Q latest-time/Salt4 repair
and weekend attach work, so new corrected-Q submission or repair instructions
should not overlap that task.

## Decisions

### Harvest Logs And Postprocessing

Do not launch an ungated harvest tonight. Both parent jobs that matter are
still running. Harvesting terminal logs before final writes risks producing a
stale or partial admission memo.

A dependency-gated harvest job is technically possible with Slurm `afterany`,
but it is not recommended tonight:

- Salt1 nominal may continue for days, so a dependency job may simply sit.
- The selected corrected-Q job is still partly running, and AGENT-253 is active
  on related repair/attach work.
- The terminal harvest is more defensible when a fresh agent checks exact
  terminal scheduler state and chooses the correct gate/collector.

Recommended next action: first thing next session, run scheduler/accounting
checks, then perform terminal harvest only for jobs or steps that have actually
left the queue.

### Thermal UA / Nu Path

Thermal UA/Nu is not production-submittable tonight. AGENT-245 found the
refined closure-QOI path blocked by reconstructed-`T` parsing / `T` field
problems. AGENT-248 proved pressure-only extraction works for Salt2 medium/fine,
but that does not admit thermal UA/HTC/Nu.

Recommended next action: open a focused Thermal UA/Nu repair task that:

- diagnoses reconstructed `T` on the Salt2 medium/fine refined mirrors;
- proves a small thermal sampling smoke before any full extraction;
- keeps pressure-only mesh comparison separate from thermal evidence;
- writes effective `h_eff`, `Nu_eff`, and `UA_eff` only after bracketing,
  sign, bulk-temperature, recirculation, and no-`qr` semantics are explicit.

### Time-Series Uncertainty Digest

The time-series uncertainty digest is ready to run as a lightweight analysis or
writer task, but it does not need Slurm. AGENT-244 already produced the
underlying package in a few minutes locally.

Recommended next action: create a compact digest for admitted Salt2/3/4 with:

- mean value;
- autocorrelation-corrected SEM;
- oscillation amplitude / RMSE about trend;
- drift over the analysis window;
- steady-state verdict;
- a note that `total_Q` is a near-zero residual and should be interpreted in
  absolute W, not only relative error.

## Carry Forward

- Leave `3282992` and surviving `3288671` steps running.
- Do not submit new corrected-Q jobs outside AGENT-253 coordination.
- Do not submit Thermal UA/Nu until the reconstructed-`T` repair smoke passes.
- Time-series digest can be assigned immediately next session as a no-Slurm
  analysis/writer task.
