# AGENT-097 Raw Journal

## Context

User requested three specific changes on `2026-06-22`:

1. stop wasting whole nodes on the corrected continuation relaunch;
2. restore the Salt bracket mutation jobs and the packed Salt optimum wave;
3. treat Water `4 x 64` packing as a pilot and shift follow-on science
   emphasis toward heater/cooler boundary behavior rather than insulation-only
   variation.

## Observed Output

- `.agent/BOARD.md` was newer than the launcher files, but the only active
  overlapping task was `AGENT-096` on the paper-side Salt analysis draft, so
  the June 18/19 run-control scope was still free to claim.
- The corrected continuation relaunch jobs were still four one-node jobs:
  `3250696`, `3250697`, `3250699`, `3250700`.
- `sacct` on the replacement jobs later showed:
  - `3250776` allocates one `256`-CPU node and runs four `64`-CPU `foamRun`
    steps (`.0`-`.3`)
  - `3250777` allocates one `256`-CPU node and runs three `64`-CPU `foamRun`
    steps (`.0`-`.2`)
- The Salt bracket and optimum jobs were absent from the live queue before the
  relaunch pass.
- The staged Water 1/3/4 continuation cases still had `purgeWrite 5`.
- The staged Salt bracket and optimum cases also still had `purgeWrite 5`.

## Actions

- Claimed `AGENT-097` for the packed relaunch scope.
- Added:
  - `scripts/run_packed_salt_continuation_wave.sbatch`
  - `scripts/run_packed_water_continuation_wave.sbatch`
- Raised all active June 18 continuation, June 19 bracket, and June 19 optimum
  staged cases to `purgeWrite 21`.
- Canceled the standalone continuation relaunch jobs:
  - `3250696`
  - `3250697`
  - `3250699`
  - `3250700`
- Submitted through `login3`:
  - `3250777` `ethan_salt_contpack`
  - `3250776` `ethan_water_contpilot`
  - `3250783` `ethan_s2j_hiqins`
  - `3250779` `ethan_s2j_loqins`
  - `3250782` `ethan_s3j_hiqins`
  - `3250781` `ethan_s3j_loqins`
  - `3250778` `ethan_s4j_hiqins_r3`
  - `3250780` `ethan_s4j_loqins_r3`
  - `3250784` `ethan_salt_optpack`
- Updated the June 18 / June 19 campaign manifests, READMEs, and TODOs to
  record the packed layout, new job IDs, the Water pilot note, and the new
  heater/cooler-focused follow-on intent.

## Interpretation

- The packed continuation relaunch is behaving as intended so far. The Water
  job is the clearest proof because `sacct` already shows all four independent
  `64`-rank solver steps under one job allocation.
- The Salt continuation pack still reserves a full node, but it has collapsed
  three prioritized continuations onto that node instead of wasting three full
  nodes.
- The Salt bracket wave is now a true six-case boundary bracket rather than the
  earlier four-case outer bracket plus deferred Salt 3 midpoint.
- The optimum-insulation wave is back in the queue, but it should be treated as
  secondary support unless later results show insulation dominates the boundary
  behavior targets more than expected.

## Contradictions / Boundaries

- The current readable case tree still does not prove a clean cooler-`h`
  mutation path. The active Salt bracket remains heater-plus-insulation only.
- The six bracket jobs still each allocate full nodes. They were restored fast,
  but not yet repacked.
- Water `4 x 64` packing is only a startup-success pilot so far. No memory or
  long-runtime stability claim is justified yet.

## Next Suggested Actions

- Inspect `3250776` for memory pressure, write completeness, and solver health
  before generalizing the Water `4 x 64` pattern.
- If the six Salt bracket cases stay healthy, decide whether a packed bracket
  launcher is worth building to cut node count.
- Isolate a reproducible cooler-side mutation path if heater/cooler boundary
  behavior remains the main next science target.
