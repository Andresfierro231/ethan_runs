# AGENT-095 Raw Journal — Corrected Continuation Relaunch

## 2026-06-22

- The user wanted the continuation jobs back up immediately but also raised the
  right concern: `purgeWrite 30` is probably more storage than we need.
- Measured the real restart-time footprint on disk from the live continuation
  roots:
  - each saved retained time was about `510 MB` per case
- That made the relaunch choice simple:
  - the late-window target is `20 s`
  - with `writeInterval 1`, preserving `21` retained times is the minimum
    contract that spans `20 s`
  - so `purgeWrite 21` is the right compromise, not `30`
- Patched only the four continuation roots that matter for the immediate
  science lane:
  - Salt 2 Jin
  - Salt 3 Jin
  - Salt 4 Jin
  - Water 2
- Salt bracket and optimum jobs stayed off because they are not the immediate
  blocker-clearing lane.

## Relaunch notes

- The first resubmission attempt failed because this scheduler now requires an
  explicit `-t`.
- Reused the original walltimes from the campaign manifest:
  - Salt jobs: `120:00:00`
  - Water 2: `72:00:00`
- Successful corrected relaunch job IDs:
  - `3250696` `ethan_s2j_cont`
  - `3250699` `ethan_s3j_cont`
  - `3250700` `ethan_s4j_cont`
  - `3250697` `ethan_w2_cont`

## End state

- The minimal corrected continuation subset is running again.
- The retained-window science target is now feasible from the restart policy.
