---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/RUNNING.md
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/run_two_tap_staged_endpoint_sampling.sh
  - tools/analyze/build_two_tap_staged_endpoint_sampler.py
tags: [pressure-ledger, two-tap, raw-endpoints, scheduler, blocker]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-ENDPOINT-LAUNCH-HARVEST.md
  - imports/2026-07-18_two_tap_endpoint_launch_harvest.json
  - .agent/blockers.yml
task: TODO-TWO-TAP-ENDPOINT-LAUNCH-HARVEST
date: 2026-07-18
role: Hydraulics/cfd-pp/Scheduler/Implementer/Tester/Writer
type: journal
status: complete
---
# Two-Tap Endpoint Launch Harvest

## Attempted

Claimed a launch/harvest row for the completed staged two-tap endpoint sampler,
validated the generated runner and sbatch script, submitted through `login3`
after direct `sbatch` reported that compute-node submission was unavailable,
and monitored Slurm terminal states. After the first failure exposed a staging
layout bug, corrected the generator, regenerated the package, retested, and
submitted the single board-authorized replacement job.

## Observed

Job `3302384` failed quickly. The Salt2 `foamPostProcess` log reported that
OpenFOAM could not detect a processor number for the staged
`constant/polyMesh/points` file because the first runner symlinked decomposed
content into a root-like case path.

Job `3302388` used the reconstructed staging path and reached `reconstructPar`,
but failed because staged `system/decomposeParDict` was absent. The source Salt2
continuation case does contain `system/decomposeParDict`; the staged copy lost
it because the runner created `system/` before checking whether source `system`
needed to be copied.

No VTK endpoint files were created and no raw endpoint pressure/velocity rows
were harvested.

## Inferred

The current remaining blocker is operational staging, not a contradiction in
the two-tap raw endpoint contract. The regenerated runner now copies
`constant` and `0`, merges missing source `system` entries with `cp -an`, links
`processors64`, disables inherited `system/functions`, replaces only
`system/controlDict`, reconstructs selected fields, and then runs
`foamPostProcess`.

## Caveats

No third scheduler submission was made because the board row authorized only
the initial failed attempt plus one corrected replacement. The generated runner
is ready for a new launch row, but it is not validated by a successful Slurm
run yet. The raw endpoint CSV still contains six missing rows and must not be
used for pressure-basis, recirculation, F6, or component-K admission.

## Next Useful Actions

Open a new scheduler row for one resubmission of the regenerated runner. If it
completes with exit code `0:0`, run:

```bash
python3.11 tools/analyze/build_two_tap_staged_endpoint_sampler.py --harvest --record-job-id <job_id>
```

Then rerun:

```bash
python3.11 -m unittest tools.analyze.test_two_tap_staged_endpoint_sampler
```

Only after `raw_endpoint_pressure_velocity.csv` contains six `sampled` rows
should the pressure/velocity basis audit start.
