# Corrected Salt-Q Time-Precision Rerun

Date: `2026-07-13`
Task: `AGENT-290`

## Observation

Job `3293441` launched the selected corrected Salt-Q four-row continuation, but
all four `foamRun` steps failed in `Foam::Time::operator++()`. The failure was
not a physics divergence. The common cause was OpenFOAM time-directory naming:
large restart times plus adaptive timesteps produced names such as
`10291.0613496932601`, and `timeFormat general`/`timePrecision 12` could not
distinguish the next time names safely.

## Repair Path

The first repair attempt raised `timePrecision` to `17` and explicitly started
from the integer restarts. Job `3293739` showed why that was insufficient:
OpenFOAM tried to increase precision from `17` to `18`, then hit its maximum.

The second repair attempt switched to `timeFormat fixed` but kept
`startFrom startTime`. Job `3293765` showed why that was also wrong:
OpenFOAM looked for a fixed-formatted start-time directory and failed to find
restart object `T`, because the existing processor restart directories are
integer names.

The third repair attempt kept `timeFormat fixed` but changed to
`startFrom latestTime`. Job `3293782` also failed with missing restart object
`T`, so fixed-format restart naming is not suitable for these integer restart
directories.

The final launcher contract is:

- explicitly patch the intended integer restart field from the manifest;
- require the selected processor restart directory to exist and equal the
  intended integer restart;
- use `startFrom startTime` with that exact integer `startTime`;
- use `timeFormat general` and `timePrecision 6`, matching the documented
  July 10 Salt4 recovery that advanced from an integer restart after higher
  precision attempts failed;
- run the reusable preflight checker before `foamRun`.

## Validation

Local validation passed before resubmission:

- Python compile for the preflight checker.
- Seven focused preflight test functions run manually because `pytest` is not
  installed in the current environment.
- `bash -n` for the selected continuation launcher.
- Four selected staged cases passed the runtime/Q preflight with
  `overall_ok=True`.

## Scheduler

Submitted `3293924` from `login3` at `2026-07-13T17:03:55-05:00`. The job
started on `c318-016`. After about 2.5 minutes of top-level runtime and
`00:02:29` of each `foamRun` step, `3293924.0`-`.3` were still `RUNNING`;
all four case logs had advanced past their integer restart times without the
earlier OpenFOAM time-name fatal error.
