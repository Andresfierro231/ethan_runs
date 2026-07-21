---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/raw_endpoint_pressure_velocity.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/RUNNING.md
tags: [pressure-ledger, two-tap, raw-endpoints, scheduler]
related:
  - .agent/journal/2026-07-18/two-tap-endpoint-resubmit-harvest.md
  - imports/2026-07-18_two_tap_endpoint_resubmit_harvest.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-ENDPOINT-RESUBMIT-HARVEST
date: 2026-07-18
role: Hydraulics/cfd-pp/Scheduler/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-TWO-TAP-ENDPOINT-RESUBMIT-HARVEST Status

## Objective

Execute the two-tap `corner_lower_right` endpoint sampling contract on staged
copies only, harvest the raw pressure/velocity/recirculation rows, and preserve
the no-F6/no-component-K guardrails.

## Outcome

Complete. The single authorized resubmission job `3302464` reconstructed and
postprocessed Salt2/Salt3/Salt4 staged copies and wrote all six endpoint VTK
surfaces. Slurm reported `FAILED` with exit code `1:0` because the in-job
Python harvest parser did not yet support OpenFOAM's wrapped
`POLYGONS`/`FIELD attributes` VTK layout. After fixing the parser, local
harvest from the staged VTKs succeeded.

Final package state:

- `raw_endpoint_pressure_velocity.csv`: six `sampled` rows.
- `raw_endpoint_surface_file_manifest.csv`: six existing VTK files.
- `summary.json`: `raw_sampled_rows=6`, `raw_missing_rows=0`,
  `last_harvest_job_id=3302464`.
- `sampler_readiness_or_failure.csv`: three `raw_endpoint_sampled` rows with
  next action `run pressure/velocity basis audit`.

## Changes Made

- Claimed and completed `TODO-TWO-TAP-ENDPOINT-RESUBMIT-HARVEST` on
  `.agent/BOARD.md`.
- Fixed `tools/analyze/build_two_tap_staged_endpoint_sampler.py` VTK parsing
  for wrapped `POLYGONS` and `FIELD attributes` cell data.
- Updated `tools/analyze/test_two_tap_staged_endpoint_sampler.py` for harvested
  package state and wrapped OpenFOAM VTK fixtures.
- Regenerated the sampler work product with harvested rows.
- Updated `RUNNING.md`, `.agent/blockers.yml`, and
  `operational_notes/maps/pressure-and-momentum-budget.md`.

## Validation

- `bash -n work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/run_two_tap_staged_endpoint_sampling.sh`
  passed.
- `bash -n work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/submit_two_tap_staged_endpoint_sampling.sbatch`
  passed.
- `python3.11 -m unittest tools.analyze.test_two_tap_staged_endpoint_sampler`
  passed: 7 tests.
- `python3.11 tools/analyze/build_two_tap_staged_endpoint_sampler.py --harvest --record-job-id 3302464`
  passed with six sampled rows.
- `sacct -j 3302464 --format=JobID,JobName,Partition,State,ExitCode,Elapsed,NodeList`
  reported Slurm job `3302464` as `FAILED` `1:0` after `00:06:58`; this is
  recorded as the old in-job parser failure after VTK generation, not as missing
  raw surfaces.
- `python3.11 tools/docs/build_repo_index.py --check` passed: blocker register
  OK with 12 entries. Generated index files were not refreshed.

## Unresolved Blockers

- Raw endpoint surface availability is resolved.
- Pressure/velocity basis audit, straight-reference/component isolation,
  same-QOI UQ, F6 governance, and component-K admission remain separate future
  tasks.

## Guardrails

Native CFD/OpenFOAM source outputs were not mutated. Registry/admission state
was not mutated. Fluid and external repositories were not edited. Generated
docs index files were not refreshed. No solver continuation, F6 fit,
component-K admission, model selection, or endpoint-pressure invention was
performed.
