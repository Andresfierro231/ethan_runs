---
provenance:
  - .agent/status/2026-07-13_AGENT-290.md
  - .agent/journal/2026-07-13/corrected-salt-q-time-precision-rerun.md
  - imports/2026-07-13_corrected_salt_q_time_precision_rerun.json
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/README.md
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/TODO.md
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/selected_submitted_jobs.csv
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/logs/selected_runtime_preflight_3293924.csv
tags: [salt-q-perturbation, admission, steady-state, scheduler-handoff]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/07-26/10/2026-07-10_overnight_submission_decision_addendum.md
  - operational_notes/07-26/13/2026-07-13_salt_q_four_row_packed_continuation.md
  - .agent/journal/2026-07-13/corrected-salt-q-time-precision-rerun.md
task: AGENT-306
date: 2026-07-13
role: Coordinator/Writer
type: operational_note
status: complete
supersedes: []
superseded_by:
---
# Tomorrow Corrected Salt-Q Live Job Handoff

## Current State

The repaired selected corrected Salt-Q continuation is job `3293924`
(`saltq_sel_cont`). It was submitted from `login3` at
`2026-07-13T17:03:55-05:00` and started on `c318-016`.

At the latest AGENT-306 check, `3293924` was still running after about
`00:35:38` top-level elapsed time, and all four `foamRun` steps were still
`RUNNING` after about `00:35:15`:

- `3293924.0`: `salt2_lo10q`
- `3293924.1`: `salt2_hi10q`
- `3293924.2`: `salt4_lo10q`
- `3293924.3`: `salt4_hi10q`

The job preflight passed inside the Slurm allocation:
`Audited 4 corrected Salt cases; failures=0`.

## Why This Job Is Different

Do not repeat the failed repair attempts from earlier today.

Failed sequence:

- `3293441`: `timeFormat general`, `timePrecision 12`; all four steps hit
  OpenFOAM maximum time-name precision.
- `3293739`: `timeFormat general`, `timePrecision 17`; OpenFOAM still tried
  precision `18`.
- `3293765`: `timeFormat fixed`, `startFrom startTime`; OpenFOAM could not find
  restart object `T`.
- `3293782`: `timeFormat fixed`, `startFrom latestTime`; OpenFOAM still could
  not find restart object `T`.

Working repair contract:

- explicit integer restart directories:
  - `salt2_jin_lo10q_corrected`: `10291`
  - `salt2_jin_hi10q_corrected`: `9674`
  - `salt4_jin_lo10q_corrected`: `11655`
  - `salt4_jin_hi10q_corrected`: `12639`
- `startFrom startTime`
- `timeFormat general`
- `timePrecision 6`
- runtime preflight requires the selected restart and rejects `latestTime` for
  explicit selected restarts.

## Monitor First Tomorrow

From the repo root:

```bash
sacct -j 3293924 --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,NodeList -P
squeue -j 3293924
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.out
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.err
```

For the four solver logs:

```bash
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt2_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt2_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q
```

Quick fatal scan:

```bash
rg -n "FOAM FATAL|Fatal error|FOAM exiting|Segmentation|floating point|cannot find file for object T|maximum precision" \
  jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.* \
  jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/*/case_stage/*/logs/log.foamRun_corrected_q
```

## Launch Decision

No additional corrected Salt-Q job was launched by AGENT-306.

Reason: `3293924` is live and all four steps survived the startup failure
window. Launching another corrected-Q continuation now would duplicate work and
complicate admission provenance. A dependency-gated harvest was also not
launched because the July 10 guidance still applies: terminal harvest should
wait until the parent job has actually exited, otherwise the admission memo can
be stale.

## If `3293924` Is Still Running

Leave it alone. Record a scheduler heartbeat in the active status/journal for
the new task that checks it. Do not cancel for ordinary drift; this job exists
to produce longer final windows.

## If `3293924` Failed

First classify the failure:

1. Read `sacct` for which step failed.
2. Tail the matching case log.
3. Search for `cannot find file for object T`, `maximum precision`, or the
   earlier `Foam::Time::operator++()` signature.

Do not revert to fixed-format restarts or higher general precision. If the
failure is a new runtime/physics failure, preserve the logs and write a new
repair note before editing the launcher.

## If `3293924` Completed Or Was Stopped

Run terminal gate work only after scheduler state is terminal. The intended
sequence is:

1. Confirm `3293924` and `3293924.0`-`.3` are terminal with `sacct`.
2. Record end state in
   `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/selected_submitted_jobs.csv`.
3. Refresh corrected-Q status:

   ```bash
   python3.11 tools/analyze/build_registry_corrected_q_status_table.py --strict-registry
   ```

4. Run an operating-point convergence gate for each of the four cases using
   `tools/analyze/assess_time_convergence.py`. This script requires `numpy`; in
   the bare AGENT-306 shell, `python3.11 tools/analyze/assess_time_convergence.py --help`
   failed with `ModuleNotFoundError: No module named 'numpy'`, so load/use the
   project Python environment that has numerical dependencies before running.
5. For `--require-moved-from`, source baseline nominal mdot from the prior
   corrected-Q gate/status package or the registry-linked nominal case evidence;
   do not guess the baseline value in a one-off command.
6. Use expected Q ratios:
   - `salt2_lo10q`: `--expected-q-ratio 0.90`
   - `salt2_hi10q`: `--expected-q-ratio 1.10`
   - `salt4_lo10q`: `--expected-q-ratio 0.90`
   - `salt4_hi10q`: `--expected-q-ratio 1.10`

Example shape after verifying the baseline mdot:

```bash
python3.11 tools/analyze/assess_time_convergence.py \
  --source-id salt2_jin_lo10q_corrected \
  --case-dir jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt2_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation \
  --output-dir work_products/2026-07/2026-07-14/2026-07-14_corrected_salt_q_3293924_terminal_gate/salt2_lo10q \
  --require-moved-from VERIFIED_NOMINAL_SALT2_MDOT \
  --expected-q-ratio 0.90
```

Repeat for the other three selected cases with their case roots and ratios.

## Admission Rule

Do not admit a row only because the Slurm job completed. Admission requires:

- corrected-Q patch/root/restart provenance remains clean;
- operating-point verdict is `requalified` or equivalent row-specific
  stationary/moved evidence is documented;
- final-window drift/oscillation/uncertainty is acceptable for the intended
  closure use;
- `total_Q` residual is handled in absolute W, not inflated relative error,
  because it is a near-zero residual.

If admitted, keep display names short (`salt2_lo10q`, `salt2_hi10q`,
`salt4_lo10q`, `salt4_hi10q`) but preserve source keys in CSV/provenance.

## Useful Context To Open First Tomorrow

- `.agent/status/2026-07-13_AGENT-290.md`
- `.agent/journal/2026-07-13/corrected-salt-q-time-precision-rerun.md`
- `imports/2026-07-13_corrected_salt_q_time_precision_rerun.json`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/README.md`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/TODO.md`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/selected_submitted_jobs.csv`
- `operational_notes/maps/cfd-runs-and-admission.md`
- `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv`
