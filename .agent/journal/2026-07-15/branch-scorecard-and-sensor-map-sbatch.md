---
provenance:
  - .agent/status/2026-07-15_AGENT-442.md
  - imports/2026-07-15_branch_scorecard_and_sensor_map_sbatch.json
tags: [journal, AGENT-442, sbatch, branch-scorecard, sensor-map]
task: AGENT-442
date: 2026-07-15
type: journal
status: complete
---
# Branch Scorecard And Sensor Map sbatch

User requested overnight execution for:

- branch-specific ordinary-pipe scorecard excluding upcomer;
- TP2/TW10 sensor-map refresh;
- documented overnight recommendations after local validation.

## Actions

1. Claimed AGENT-442 with a narrow CPU-only scheduler scope.
2. Confirmed AGENT-439 already submitted the documented M3+TS, val_salt2, and
   matched-plane/onset sbatch jobs: `3297844`, `3297842`, `3297843`.
3. Confirmed AGENT-440 already submitted staged closure-QOI/pressure sbatch
   job `3297845`.
4. Built `tools/analyze/build_branch_specific_ordinary_pipe_scorecard.py`.
5. Built `tools/analyze/build_sensor_tp2_restore_scorecard.py`.
6. Added focused tests for both builders.
7. Ran both builders and tests locally.
8. Submitted one CPU-only development-partition sbatch job through `login3`
   because `sbatch` is unavailable on compute nodes.
9. Confirmed Slurm job `3297849` completed successfully.

## Observed Results

Branch scorecard:

- Reviewed `28` current evidence rows.
- Admitted `0` ordinary-pipe coefficient fit rows.
- Reviewed `25` upcomer evidence rows.
- Admitted `0` upcomer ordinary-pipe fit rows.
- Preserved upcomer as recirculation/hybrid/onset lane only.

Sensor refresh:

- TP2 restored as gated post-solve scoring candidate at
  `right_downcomer_bottom_horizontal_junction`.
- TP2 remains `runtime_temperature_allowed=false` and `fit_allowed=false`.
- Aggregate count changes from `5 TP + 10 TW` to `6 TP + 10 TW` only after
  TP2 finite prediction/projection gates pass.
- TW10 remains excluded until an active-HX shell-state temperature exists.

## Validation

- Local builders passed.
- Local unit tests passed: `9` tests.
- Sbatch job `3297849` reran both builders and all tests successfully.

No native CFD outputs, registry/admission state, generated indexes, or external
`../cfd-modeling-tools/**` paths were mutated.
