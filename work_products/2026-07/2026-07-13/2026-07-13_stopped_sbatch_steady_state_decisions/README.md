# Stopped Sbatch Steady-State Decisions

Date: `2026-07-13`

Task: `AGENT-280`

## Purpose

This package backfills explicit final-window evidence for sbatch jobs/steps that
were completed operationally or ended early during the July 13 Salt1 /
corrected-Q coordination pass.

## Answer

The earlier documentation was incomplete. Salt4 +10Q was documented with
numeric final-window evidence as **not steady** in `AGENT-274`, but the stopped
Salt1 nominal, Salt1 -10Q, and Salt1 +10Q steps were not documented in one
place with enough final-window values. This package is the correction.

## Decisions

| Case | Slurm job/step | Final window | Decision |
| --- | --- | ---: | --- |
| `salt1_nominal` | `3282992.0` | `7284-7884 s` | steady enough for runtime stop; separate closure/admission context still required |
| `salt1_lo10q` | `3288671.0` | `7416-8016 s` | steady enough for runtime stop; not promoted as Salt1 corrected-Q closure-fit priority |
| `salt1_hi10q` | `3288671.1` | `4987-5587 s` | steady enough for runtime stop/freeing slot; not promoted as Salt1 corrected-Q closure-fit priority |
| `salt4_hi10q` | `3288671.5` | `12039-12639 s` | not steady; included in fresh packed job `3293441` |

## Key Quantities

- Salt1 nominal: mdot relative drift over final 600 s was at most
  `8.01e-8`; `total_Q` drift was `0 W`; monitored fluid and wall probes were
  unchanged in written final-window values.
- Salt1 -10Q: mdot relative drift was at most `3.34e-7`; `total_Q` drift was
  `0 W`; monitored fluid and wall probes were unchanged in written final-window
  values.
- Salt1 +10Q: mdot relative drift was at most `2.01e-6`; `total_Q` drift was
  `0 W`; monitored fluid and wall probes were unchanged in written final-window
  values.
- Salt4 +10Q: mdot relative drift was about `0.61-0.63%`, mdot relative span
  about `2.42-2.44%`, `total_Q` drift was `-1.59099 W`, fluid probe max drift
  was `1.45105 K`, and wall probe max drift was `1.52954 K`.

## Data

- `final_window_metrics.csv`: machine-readable mean/latest/drift/span rows for
  `total_Q`, four mdot monitors, and max temperature/wall-temperature probe
  drift summaries.
- `summary.json`: compact decision summary and future documentation rule.

## Future Rule

Any future user-approved sbatch cancellation, early stop, or "ready to
postprocess" call must include the final-window numeric evidence in the same
status/journal or operational note as the action. If the stop is for resource
scheduling rather than true terminal evidence, say so explicitly.
