# AGENT-103 Journal

Date: `2026-06-22T17:35:06-05:00`
Role: `Coordinator / Writer`
Task: `AGENT-103`

## Intent

Answer whether the current Ethan Salt runs were actually balanced by
construction, then write a durable future contract for Salt DOE children that
keeps the heat budget readable and scientifically usable.

## Observed state at start

- The readable Salt cases still expose `bc_params.cooler.h` in
  `case_config.yaml`.
- The authoritative cooling branch in the staged `0/T` files is still a
  fixed-`Q` sink on `pipeleg_upper_04_reducer`,
  `pipeleg_upper_05_cooler`, and `pipeleg_upper_06_reducer`.
- The June 19 Salt bracket children changed lower-heater `Q` and insulation,
  but did not recalculate those cooling-branch fixed sinks.
- The June 10 Salt 2 heat-audit note already preserved a near-zero late-tail
  wall-heat closure example, so runtime closure and staging invariants needed
  to be separated explicitly.

## Action

- Wrote a dedicated operational note and report package explaining the current
  mixed heat-balance contract and the evidence for it.
- Updated the June 18 continuation-wave and June 19 Salt follow-on campaign
  docs to stop treating metadata cooler `h` as a live DOE knob and to require
  explicit fixed-`Q` cooling residual bookkeeping for future Salt children.
- Added the June 22 workspace journal follow-on section so the answer is
  preserved alongside the same-day frozen-state and feature-path work.

## Completion

- The repo now states the future bookkeeping rule as
  `Q_in - Q_lost = 0`, with `Q_lost = Q_removed + Q_ambient` at the chosen
  parent reference state.
- The current six Salt bracket jobs are documented as exploratory limit probes,
  not strict balance-by-construction heater/cooler DOE children.
- Future fixed-`Q` Salt DOE children are now instructed to solve and record the
  child cooling-branch `Q_removed` residual before submission.
