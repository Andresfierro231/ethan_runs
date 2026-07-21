# Stopped Sbatch Steady-State Decisions

Date: `2026-07-13`

Task: `AGENT-280`

## Prompt

The user asked whether the sbatch jobs completed or ended early had been
documented as steady state with final-window change quantities, and requested
thorough future documentation.

## Answer

Not completely. `AGENT-274` documented Salt4 +10Q thoroughly as **not steady**,
including mdot, `total_Q`, and temperature/wall-temperature drift. The stop
decisions for Salt1 nominal, Salt1 -10Q, and Salt1 +10Q were scattered across
status notes and scheduler actions, but did not carry a single final-window
numeric table. This task fixes that gap.

## Observed Final-Window Evidence

All windows below are 600 s windows from the final available written
postProcessing samples.

| Case | Step | Window | Decision | Key evidence |
| --- | --- | ---: | --- | --- |
| `salt1_nominal` | `3282992.0` | `7284-7884 s` | steady enough for runtime stop; separate closure/admission context still required | max mdot relative drift `8.01e-8`; `total_Q` drift `0 W`; temperature/wall probes unchanged |
| `salt1_lo10q` | `3288671.0` | `7416-8016 s` | steady enough for runtime stop; not promoted as Salt1 corrected-Q closure-fit priority | max mdot relative drift `3.34e-7`; `total_Q` drift `0 W`; temperature/wall probes unchanged |
| `salt1_hi10q` | `3288671.1` | `4987-5587 s` | steady enough for runtime stop/freeing slot; not promoted as Salt1 corrected-Q closure-fit priority | max mdot relative drift `2.01e-6`; `total_Q` drift `0 W`; temperature/wall probes unchanged |
| `salt4_hi10q` | `3288671.5` | `12039-12639 s` | not steady; included in fresh packed job `3293441` | mdot relative drift `0.61-0.63%`; mdot span `2.42-2.44%`; `total_Q` drift `-1.59099 W`; fluid probe drift `1.45105 K`; wall probe drift `1.52954 K` |

Machine-readable values are in
`work_products/2026-07/2026-07-13/2026-07-13_stopped_sbatch_steady_state_decisions/final_window_metrics.csv`.

## Important Boundary

For the Salt1 rows, "steady enough for runtime stop" is not the same as a full
publication or closure-fit admission. The Salt1 nominal row still needs any
intended closure/admission context documented explicitly, and Salt1 corrected-Q
rows remain lower-priority / policy-caveated versus the Salt2/Salt4 corrected-Q
bracket. The stop decision was operationally justified by flat final-window
monitors.

## Future Rule

Updated `.agent/DECISIONS.md`: every future user-approved sbatch cancellation,
early stop, or ready-to-postprocess call must document Slurm ID, case path,
final-window time bounds, mean/latest/drift/span for key mdot monitors and
`total_Q` where available, max temperature and wall-temperature drift where
available, and the steady/not-steady/admission decision. Resource-scheduling
stops must be identified as such.
