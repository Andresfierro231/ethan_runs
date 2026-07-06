# Ethan Packed Continuation And Salt Wave

Generated: `2026-06-22`

## Purpose

Replace the wasteful June 22 standalone continuation relaunch with packed
continuation nodes, restore the Salt bracket mutation wave, and requeue the
packed Salt optimum-insulation wave under the corrected `purgeWrite 21`
retention contract.

## Queue Outcome

Running:

- `3250777` `ethan_salt_contpack`
  - one node
  - cases: `salt2_jin`, `salt3_jin`, `salt4_jin`
- `3250776` `ethan_water_contpilot`
  - one node
  - cases: `water1`, `water2`, `water3`, `water4`
- `3250783` `ethan_s2j_hiqins`
- `3250779` `ethan_s2j_loqins`
- `3250782` `ethan_s3j_hiqins`
- `3250781` `ethan_s3j_loqins`
- `3250778` `ethan_s4j_hiqins_r3`
- `3250780` `ethan_s4j_loqins_r3`

Pending:

- `3250784` `ethan_salt_optpack`

Canceled to make room for the packed continuation layout:

- `3250696` `ethan_s2j_cont`
- `3250697` `ethan_w2_cont`
- `3250699` `ethan_s3j_cont`
- `3250700` `ethan_s4j_cont`

## Packed Layout Verification

`sacct` confirms the packed continuation jobs are behaving as intended:

- `3250776` allocates one `256`-CPU node and currently runs four independent
  `64`-CPU `foamRun` steps
- `3250777` allocates one `256`-CPU node and currently runs three independent
  `64`-CPU `foamRun` steps

This means the Water pilot is already exercising the requested `4 x 64`
single-node packing pattern, while the Salt continuation node is using the
requested `3 x 64` layout with one `64`-CPU slice intentionally left idle.

## Retention Contract

All active June 18 continuation, June 19 bracket, and June 19 optimum staged
cases now use:

- `writeInterval 1`
- `purgeWrite 21`

That is the smallest integer setting that preserves the target `20 s`
late-window restart horizon without returning to the earlier over-large
storage guess.

## Science Direction Captured

The June 22 campaign-note refresh makes the current intent explicit:

- use the Salt bracket wave to probe heater-side boundary behavior first
- treat the Water `4 x 64` node as a pilot that still needs inspection
- keep the packed optimum-insulation wave as supporting sensitivity evidence
- prioritize future work on heater/cooler temperature-difference extremes,
  upcomer recirculation onset, and development-length sensitivity
- keep the cooler-`h` path marked unresolved until the workspace proves a real
  readable mutation path
