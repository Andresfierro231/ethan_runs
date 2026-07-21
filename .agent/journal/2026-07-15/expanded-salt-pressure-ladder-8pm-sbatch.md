# Expanded Salt Pressure-Ladder 8 PM sbatch

Date: 2026-07-15
Task: AGENT-447

## Request

The user requested the overnight pressure-ladder postprocessing be expanded
beyond Salt2/Salt3/Salt4 nominal coverage to include Salt1 and other Salt runs
needed for training and validation, beginning at 8 PM.

## Method

I reused the proven AGENT-445 pressure-ladder structure, but created a separate
AGENT-447 package and Slurm job so the expanded Salt training/validation set
does not collide with the nominal Salt2/Salt3/Salt4 ladder already queued as
job `3297860`.

The generated runner:

1. Checks the source case, terminal processor time, OpenFOAM 13 environment,
   and 30 mesh station planes for each case.
2. Stages a local diagnostic work copy under
   `tmp/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/pressure_ladder/`.
3. Copies only `constant`, `system`, and `0` into the staged case.
4. Symlinks `processors64` from the native CFD case read-only.
5. Replaces the staged `system/controlDict` with an AGENT-447 surfaces sampler.
6. Runs `reconstructPar` and `foamPostProcess` on the staged copy only.
7. Harvests station pressure rows and adjacent-pair pressure deltas into the
   work product.

No native solver outputs are written.

## Case Selection

Included:

- Salt1 nominal, lo10q, hi10q as training candidates.
- Salt2 lo5q and hi5q as holdout perturbations only.
- Salt4 lo5q and hi5q as training perturbations.
- val_salt2 as external validation.

Deliberately not duplicated:

- Salt2/Salt3/Salt4 nominal rows, because AGENT-445 already queued them in job
  `3297860`.
- Salt2/Salt4 +/-10Q, because those remain in the corrected-Q chain and should
  be harvested from that lane rather than duplicated here.
- Legacy Salt4 `balq`/`hiins` and Salt3 low/high perturbations, because prior
  audit notes did not promote them into this training/validation pressure-ladder
  lane.

## Local Validation

Commands completed successfully:

- Python compile check for builder and test scripts.
- Package build.
- Focused package tests.
- Runner `--preflight-only`.
- Slurm script `bash -n`.

The preflight confirmed all 8 source cases, all 8 terminal processor times, all
mesh station files, and the OpenFOAM 13 environment. Each case has 30 station
planes.

## Submission

Submitted through `login3`:

`sbatch work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/scripts/submit_expanded_pressure_ladder_8pm.sbatch`

Slurm returned job `3297863`.

Last queue check:

`3297863 press_lad2 PENDING 0:00 14:00:00 2026-07-15T20:00:00 (BeginTime)`

AGENT-445 job `3297860` was also checked and was running:

`3297860 press_ladder RUNNING 4:45 8:00:00 2026-07-15T18:10:31 c318-012`

## Tomorrow Pickup

1. Check `sacct -j 3297863`.
2. If terminal and successful, run:
   `python3.11 tools/analyze/build_expanded_salt_pressure_ladder_8pm_sbatch.py --harvest --record-job-id 3297863`
3. Review `station_pressure_ladder.csv` and `adjacent_pressure_ladder.csv`.
4. Keep rows diagnostic until pressure definition, mesh/GCI, orientation,
   straight-loss subtraction, and recirculation gates admit them.
