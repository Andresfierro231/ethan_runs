---
provenance:
  - tools/analyze/build_branch_specific_ordinary_pipe_scorecard.py
  - tools/analyze/build_sensor_tp2_restore_scorecard.py
  - work_products/2026-07/2026-07-15/2026-07-15_branch_specific_ordinary_pipe_scorecard/summary.json
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_tp2_restore_tw10_exclude/summary.json
tags: [sbatch, branch-scorecard, sensor-map, overnight, AGENT-442]
task: AGENT-442
date: 2026-07-15
type: work_product_readme
status: complete
---
# Branch/Sensor Overnight sbatch

AGENT-442 submitted one CPU-only Slurm job after local validation.

## Job

- Job ID: `3297849`
- Name: `branch_sensor`
- Partition: `development`
- Node: `c309-005`
- State: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:00:01`

## Command

Submitted from `login3` because `sbatch` is not available on compute nodes:

```bash
ssh login3.ls6.tacc.utexas.edu "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-15/2026-07-15_branch_sensor_overnight_sbatch/scripts/run_branch_sensor_scorecards.sbatch"
```

## Outputs

- Branch-specific ordinary-pipe scorecard:
  `work_products/2026-07/2026-07-15/2026-07-15_branch_specific_ordinary_pipe_scorecard/`
- TP2/TW10 sensor-map refresh:
  `work_products/2026-07/2026-07-15/2026-07-15_sensor_tp2_restore_tw10_exclude/`
- Slurm stdout:
  `work_products/2026-07/2026-07-15/2026-07-15_branch_sensor_overnight_sbatch/logs/branch_sensor-3297849.out`
- Slurm stderr:
  `work_products/2026-07/2026-07-15/2026-07-15_branch_sensor_overnight_sbatch/logs/branch_sensor-3297849.err`

## Result

The branch scorecard reviewed `28` current evidence rows and admitted `0`
ordinary-pipe coefficient fit rows. The upcomer had `25` evidence rows and `0`
ordinary-pipe fit rows, preserving it as a recirculation/hybrid/onset lane.

The sensor refresh keeps TP2 and TW10 forbidden as runtime temperature inputs
and fit targets. TP2 is restored as a gated post-solve scoring candidate on
`right_downcomer_bottom_horizontal_junction`; aggregate count changes from
`5 TP + 10 TW` to `6 TP + 10 TW` only after finite prediction/projection gates
pass. TW10 remains excluded until an active-HX shell-state model exists.

## Other Overnight Recommendations

AGENT-442 did not duplicate active scheduler work:

- AGENT-439 already submitted `3297844` (`m3ts_score`), `3297842`
  (`val_s2_ext`), and `3297843` (`pm5_onset`), all dependency-gated behind
  `3295438`.
- AGENT-440 already submitted `3297845` (`cqp_stage`) for staged closure-QOI/
  pressure postprocessing.

## Validation

- Local builders passed before submission.
- Local tests passed: `9` tests.
- Slurm job reran both builders and the same `9` tests successfully.

No OpenFOAM job was launched by AGENT-442. Native CFD outputs,
registry/admission state, generated indexes, and external
`../cfd-modeling-tools/**` were not mutated.
