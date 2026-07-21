---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/RUNNING.md
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/logs/salt2_mainline_reconstructPar.log
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/logs/salt2_mainline_foamPostProcess.log
tags: [pressure-ledger, two-tap, raw-endpoints, scheduler, blocker]
related:
  - .agent/journal/2026-07-18/two-tap-endpoint-launch-harvest.md
  - imports/2026-07-18_two_tap_endpoint_launch_harvest.json
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/RUNNING.md
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-ENDPOINT-LAUNCH-HARVEST
date: 2026-07-18
role: Hydraulics/cfd-pp/Scheduler/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-TWO-TAP-ENDPOINT-LAUNCH-HARVEST Status

## Objective

Launch the completed `corner_lower_right` two-tap raw endpoint sampler,
monitor terminal state, harvest six endpoint VTK rows if the job succeeds, or
record failure status and next actions if it does not.

## Outcome

Complete as a launch/diagnosis row, with raw endpoint sampling still blocked.
Two task-owned Slurm attempts were submitted and both failed before producing
VTK endpoint surfaces:

- Job `3302384`: `FAILED` `1:0` after `00:00:11` on `c318-019`; OpenFOAM
  rejected the first staged case because root-level `constant/polyMesh` looked
  like decomposed processor content.
- Job `3302388`: `FAILED` `1:0` after `00:00:15` on `c318-019`;
  `reconstructPar` failed because the staged `system/` directory did not carry
  the source `decomposeParDict`.

The sampler generator and regenerated runner now merge missing source
`system` entries into the staged copy before replacing `system/controlDict`
with the task controlDict. No third scheduler submission was made under this
row.

## Changes Made

- Updated `.agent/BOARD.md` with the active launch row, the two submitted job
  IDs, and the no-third-submit guardrail.
- Added `.agent/blockers.yml` entry
  `two-tap-raw-endpoint-sampling-pending`.
- Fixed `tools/analyze/build_two_tap_staged_endpoint_sampler.py` so generated
  staging copies retain source `system` dictionaries.
- Regenerated
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/**`.
- Added and updated
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/RUNNING.md`.
- Updated `operational_notes/maps/pressure-and-momentum-budget.md`.

## Validation

- `bash -n work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/run_two_tap_staged_endpoint_sampling.sh`
  passed.
- `bash -n work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/submit_two_tap_staged_endpoint_sampling.sbatch`
  passed.
- `python3.11 tools/analyze/build_two_tap_staged_endpoint_sampler.py` passed.
- `python3.11 -m unittest tools.analyze.test_two_tap_staged_endpoint_sampler`
  passed: 6 tests.
- `python3.11 tools/docs/build_repo_index.py --check` passed: blocker
  register OK with 12 entries. Generated index files were not refreshed.
- `sacct -j 3302384,3302388 --format=JobID,JobName,Partition,State,ExitCode,Elapsed,NodeList`
  confirmed jobs `3302384` and `3302388` failed with exit code `1:0`.

## Unresolved Blockers

- Six raw endpoint rows remain `missing_raw_surface_file`; no endpoint VTK
  surfaces were harvested.
- A new board row is required before another `two_tap_ep` scheduler submission.
- After a future successful harvest, pressure/velocity basis audit,
  straight-reference/component isolation, recirculation admission, same-QOI UQ,
  F6 governance, and component-K admission must still remain separate tasks.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Fluid and external repositories were not edited. Generated docs index
files were not refreshed. No solver continuation, F6 fit, component-K
admission, model selection, or endpoint-pressure invention was performed.
