# Ethan Corrected Continuation Relaunch

Generated: `2026-06-22`

## Purpose

Restart the minimal continuation subset immediately after the June 22 stop
decision, but with the smallest retention change that still satisfies the
science requirement for a preserved `20 s` late window.

## Storage Decision

Measured retained restart footprint:

- about `510 MB` per saved time per case

Therefore:

- `purgeWrite 30` would be larger than needed
- `purgeWrite 21` is the smallest value that preserves a full `20 s` span at
  `writeInterval 1`

Estimated retained restart footprint at `purgeWrite 21`:

- about `10.7 GB` per case
- about `42.8 GB` across the four relaunched cases

## Relaunched Jobs

- `3250696` `ethan_s2j_cont`
- `3250699` `ethan_s3j_cont`
- `3250700` `ethan_s4j_cont`
- `3250697` `ethan_w2_cont`

All four were resubmitted through `login3` with explicit walltimes:

- Salt: `120:00:00`
- Water 2: `72:00:00`

## Scope Boundary

Only the continuation subset was restarted:

- Salt 2 Jin
- Salt 3 Jin
- Salt 4 Jin
- Water 2

Not restarted in this pass:

- Salt heater-plus-insulation bracket jobs
- packed optimum-thickness job

## Configuration Change

Patched in each relaunched continuation root:

- `writeInterval 1`
- `purgeWrite 21`

This keeps the original `1 s` write cadence but extends the retained restart
window from about `4 s` to a full `20 s`.
