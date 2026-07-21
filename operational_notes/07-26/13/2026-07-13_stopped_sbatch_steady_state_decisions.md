# Stopped Sbatch Steady-State Decisions

Date: `2026-07-13`

## Correction

The prior notes did not put all stopped sbatch steady-state decisions in one
place with final-window drift values. This note and the AGENT-280 work product
are the backfill.

## Summary

- Salt1 nominal, Salt1 -10Q, and Salt1 +10Q were flat enough for the runtime
  stop decisions.
- Salt4 +10Q was not steady and was correctly included in the new packed job
  `3293441`.

## Final-Window Calls

| Case | Step | Final window | Call |
| --- | --- | ---: | --- |
| `salt1_nominal` | `3282992.0` | `7284-7884 s` | steady runtime stop; max mdot relative drift `8.01e-8`; `total_Q` drift `0 W` |
| `salt1_lo10q` | `3288671.0` | `7416-8016 s` | steady runtime stop; max mdot relative drift `3.34e-7`; `total_Q` drift `0 W` |
| `salt1_hi10q` | `3288671.1` | `4987-5587 s` | steady runtime stop/free slot; max mdot relative drift `2.01e-6`; `total_Q` drift `0 W` |
| `salt4_hi10q` | `3288671.5` | `12039-12639 s` | not steady; max mdot relative drift `0.00627`, `total_Q` drift `-1.59099 W`, fluid/wall probe drift `1.45105/1.52954 K` |

Full values:
`work_products/2026-07/2026-07-13/2026-07-13_stopped_sbatch_steady_state_decisions/final_window_metrics.csv`.

## Future Rule

Every future sbatch stop/ready-to-postprocess decision must include numeric
final-window evidence in the same status/journal/operational note as the action.
Do not rely on chat context alone.
