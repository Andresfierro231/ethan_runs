---
provenance:
  - .agent/status/2026-07-21_TODO-HIGH-HEAT-SALT4-STEADY-RELAUNCH-2026-07-21.md
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_steady_relaunch_manifest.csv
tags: [openfoam, salt4, high-heat, relaunch]
related:
  - imports/2026-07-21_high_heat_salt4_steady_relaunch.json
task: TODO-HIGH-HEAT-SALT4-STEADY-RELAUNCH-2026-07-21
date: 2026-07-21
role: Scheduler/cfd-pp/Implementer/Tester/Writer
status: complete
---
# High-Heat Salt4 Steady Relaunch

## Attempted

Relaunched the high-heat Salt4 bracket/probe cases after jobs `3299610` and
`3299620` timed out. The relaunch used the latest completed integer
`processors64` fields rather than restarting from `10000`.

## Observed

The previous run left usable restart fields at:

- `q0500`: `11658`
- `q1000`: `11031`
- `q1500`: `10795`
- `q3x`: `11395`

Pre-submit preflight and the in-job preflight both audited all four cases with
zero failures. Submitted job `3308712` from `login1`; early accounting showed
the parent job and four `foamRun` steps running on `c318-017`.

## Inferred

The main relaunch correction is avoiding the stale `10000` restart. Packing all
four cases into one 256-task allocation also avoids the split-job state where
`q3x` and the bracket pack must be tracked separately.

## Caveats

This is a solver continuation only. It does not make a steady-state claim, a
low-recirculation claim, a pressure/F6 admission, or a predictive-model release.
Endpoint use requires a separate terminal harvest/disposition row.

## Next Actions

Monitor job `3308712`. After it is terminal, repeat the drift assessment for
mdot, temperature probes, wall temperature probes, `total_Q.dat`, and summed
`wallHeatFlux.dat` over the latest available window.
