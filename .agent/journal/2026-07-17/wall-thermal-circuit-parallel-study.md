---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score/README.md
tags: [journal, AGENT-522, wall-circuit, test-section, parallel-fluid]
related:
  - .agent/status/2026-07-17_AGENT-522.md
  - predictive-wall-test-section-submodels
task: AGENT-522
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Wall Thermal-Circuit Parallel Study

## Why This Exists

AGENT-498 showed PB2/PB3 local passive distribution candidates improve mdot but
make TP/TW/all-probe shape much worse than M3. AGENT-513 then showed changing
upcomer passive/test-section drive selectors to Fluid-computed wall states does
not fix the blocker. AGENT-511 completed during this session and showed
heater-source redistribution also remains unadmitted.

AGENT-522 opens the next non-duplicative study: heated-incline wall-state drive
and explicit test-section-only wall/fluid coupling, with parallel Fluid scoring
so the 24 candidate/case rows do not run serially.

## Implementation

Added `tools/analyze/build_wall_thermal_circuit_study.py` and
`tools/analyze/test_wall_thermal_circuit_study.py`.

The builder emits four candidates:

- `HIW1_heated_incline_pipe_outer_wall_drive`
- `HIW2_heated_incline_outer_surface_drive`
- `TSC1_test_section_only_pipe_outer_wall_drive`
- `TSC2_test_section_only_outer_surface_drive`

Each is paired with lumped and segmented HX candidates across Salt2/Salt3/Salt4.
The runtime contract uses setup external-boundary rows, PB2 Salt2 shape, Fluid
computed wall-state drive selectors, and Salt2 cooler alpha_UA. Salt3/Salt4
probe/wall/flux evidence remains scoring-only.

## Scheduler Notes

The requested attach-to-existing-allocation smoke was attempted only as:

`srun --jobid=3300966 --overlap -n1 hostname`

It failed repeatedly with `Error creating slurm stream socket: Operation not
permitted` and was interrupted. No Fluid solve or repo write ran through that
overlap attempt. `sacct` then showed AGENT-511 job `3300966` completed.

Direct `sbatch` from this compute-node shell failed because `sbatch` is not
available on compute nodes. Submission through `login1` initially failed until
the `ASC23046` account was declared. Final submission succeeded:

`Submitted batch job 3301052`

Final monitor shows `3301052` completed in `00:05:37` with exit code `0:0` on
`c318-009`. The job ran the focused tests, the parallel `--run-fluid` build, and
the `--reuse-existing-coupled` refresh.

## Coupled Result

The AGENT-522 scorecard has `24/24` completed rows and `0/8` admitted
candidates. The blocker remains open.

The most favorable rows still fail the full gate:

- `TSC2_test_section_only_outer_surface_drive_PLUS_HX_SEGMENTED_UA_NTU_N16`
  has validation TP delta only `0.12844226 K` worse than M3 and improves mdot,
  but TW is `45.47524243 K` worse and all-probe is `36.56854139 K` worse.
- `TSC1` keeps strong mdot improvement but still regresses TP, TW, and
  all-probe on both validation and holdout.
- `HIW1` is not useful: it worsens mdot and temperature, with Salt4 TW5 up to
  `78.64861796 K` worse than M3.

Probe-level evidence contains `408` localization rows, `272` validation/holdout
probe deltas, and `160` role/segment summaries. Probe gates are `206` fail,
`34` pass, and `32` not compared.

## Next Actions

Do not spend the next pass on passive wall-state drive selectors. AGENT-498,
AGENT-513, AGENT-511, and AGENT-522 now show the same pattern: mdot can improve,
but the temperature field shape is wrong. Next candidates should attack axial
mixing/upcomer stratification, sensor-map/coordinate correctness, or explicit
wall/fluid thermal storage/coupling requiring a new Fluid API row.
