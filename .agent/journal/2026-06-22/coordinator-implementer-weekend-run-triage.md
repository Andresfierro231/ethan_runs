# AGENT-094 Raw Journal — Weekend Run Triage

## 2026-06-22

- Re-read the live blocker and modeling handoff packages before touching the
  queue. The core decision rule stayed the same: the continuation lane was only
  worth keeping if it could produce a preserved retained field window long
  enough for the straight-row late-window rebuild.
- Checked current queue state first and confirmed the live science jobs were:
  - June 18 continuations on Salt 2 Jin, Salt 3 Jin, Salt 4 Jin, and Water 2
  - June 19 Salt 2 / Salt 4 heater-plus-insulation bracket jobs
  - a still-pending packed Salt optimum-thickness job
- Verified from the live case roots that both the June 18 continuation wave and
  the June 19 Salt bracket wave shared the same restart retention contract:
  - `writeControl adjustableRunTime`
  - `writeInterval 1`
  - `purgeWrite 5`
- That made the main science decision straightforward:
  - these runs can preserve only the last `5` retained field writes
  - the straight-section blocker was explicitly asking for a preserved last
    window near `20 s`
  - therefore more wallclock runtime could improve endpoint convergence and
    scalar histories, but it could not satisfy the stated late-window release
    criterion

## Final preserved field windows at cancellation

- June 18 continuation wave:
  - Salt 2 Jin: `4871-4875 s`
  - Salt 3 Jin: `4804-4808 s`
  - Salt 4 Jin: `7683-7687 s`
  - Water 2: `6061-6065 s`
- June 19 Salt bracket wave:
  - Salt 2 hiq/hiins: `4425-4429 s`
  - Salt 2 loq/loins: `4399-4403 s`
  - Salt 4 hiq/hiins retry: `5789-5793 s`
  - Salt 4 loq/loins retry: `5789-5793 s`

## Important nuance

- The runs were not completely useless. The case roots still preserve long
  histories for some scalar and line-sample artifacts such as:
  - `total_Q.dat`
  - probe files
  - `velocity_profiles/**`
- But those artifacts do not replace the retained restart-field window needed
  by the straight-row rebuild path written into the blocker plan.
- The queue therefore became a compute-cost question rather than an ambiguity:
  keep paying for endpoint-only convergence evidence, or stop and relaunch with
  the right retention policy. I chose to stop.

## Queue action

- Stopped the active science jobs:
  - `3244950`
  - `3244951`
  - `3244954`
  - `3244957`
  - `3246561`
  - `3246564`
  - `3250524`
  - `3250525`
  - `3250526`
- `sacct` then confirmed cancellation timestamps at `2026-06-22 10:31 CDT`.
- I did not touch the older `DependencyNeverSatisfied` queue clutter because
  that is queue hygiene, not part of the scientific triage decision.

## End state

- Wrote the dated triage package.
- Marked AGENT-094 complete.
- Left the next implementation step explicit: relaunch only the minimal
  continuation subset with corrected restart retention and keep the bracket wave
  staged but off until the corrected continuation evidence is analyzed.
