# Journal: Pressure-Ladder Unlock Plan And sbatch

Date: 2026-07-15
Task: AGENT-445

## Work Performed

Claimed AGENT-445 to move beyond AGENT-440's two-tap diagnostic extraction.
Built a staged pressure-ladder package that samples all 30 mesh-centerline
station planes for Salt2/Salt3/Salt4 coarse mainline cases.

This postprocessing targets tomorrow's actual hydraulic unlock needs:

- pressure orientation by branch;
- adjacent straight/developing pressure gradients;
- straight-loss subtraction before component K;
- reverse-area masks before true coefficient fits;
- branch-specific diagnostic versus fit labels.

## Local Checks

Generated the package, compiled Python, ran focused tests, and ran the runner in
`--preflight-only` mode. Preflight verified the three source cases, processor
times, station files, and OF13 environment without launching heavy OpenFOAM on
the current shell.

Fixed one preflight bookkeeping issue before submission: preflight-only now
exits before harvest, so missing/stale station rows are not confused with job
outputs.

## Submission

Submitted through `login3.ls6.tacc.utexas.edu`:

```bash
ssh login3.ls6.tacc.utexas.edu 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/scripts/submit_pressure_ladder.sbatch'
```

Slurm returned job `3297860` (`press_ladder`). Initial state was pending on
priority.

## Follow-Up

Tomorrow:

```bash
sacct -j 3297860 --format=JobID,JobName%30,State,Elapsed,ExitCode,NodeList%20
python3.11 tools/analyze/build_pressure_ladder_unlock_sbatch.py --harvest --record-job-id 3297860
```

Then build pressure orientation and straight-loss subtraction screens from
`station_pressure_ladder.csv` and `adjacent_pressure_ladder.csv`.
