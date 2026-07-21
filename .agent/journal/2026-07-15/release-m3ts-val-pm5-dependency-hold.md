---
provenance:
  - .agent/status/2026-07-15_AGENT-444.md
  - imports/2026-07-15_release_m3ts_val_pm5_dependency_hold.json
tags: [journal, AGENT-444, scheduler, dependency-release]
task: AGENT-444
date: 2026-07-15
type: journal
status: complete
---
# Release M3TS / val_salt2 / PM5 Dependency Hold

User suspected the dependency chain had failed and asked whether the jobs had
crashed or should be resubmitted.

## What I Checked

- `squeue -u andresfierro231`
- `sacct -j 3293924,3295438,3297842,3297843,3297844,3297845,3297849`
- `scontrol show job 3297844`
- `scontrol show job 3297842`
- `scontrol show job 3297843`

## Finding

The jobs had not crashed. Earlier `squeue` showed `Dependency`, because
`3293924` was still running and `3295438` was still dependency-held. At the
later `scontrol` check, all three AGENT-439 jobs had `Dependency=(null)`.

Current observed states:

- `3297844` / `m3ts_score`: pending for priority, scheduled start
  `2026-07-15T20:30:00`.
- `3297842` / `val_s2_ext`: pending for priority, scheduled start
  `2026-07-15T20:30:00`.
- `3297843` / `pm5_onset`: running on `c318-012`.

## Action

Did not resubmit duplicate jobs. Did not cancel jobs. Updated the AGENT-439
package documentation/table so tomorrow's agent sees that the original job IDs
are dependency-cleared and should be monitored directly.
