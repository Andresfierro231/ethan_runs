# Salt1 Combined Rigor Relaunch Plan

Date: `2026-07-08`
Task: `AGENT-222`

## User Request

Evaluate whether to cancel the running Salt1 nominal continuation, add the
lightweight monitor/replay job, and relaunch both in a single Slurm allocation.

## Decision

Do not cancel the live Salt1 job right now.

Reason:

- `3282992` is running and actively advancing.
- The account rejected a 12-SU lightweight monitor/replay job because queued
  and running jobs already over-encumber the project allocation.
- Canceling `3282992` would free only the same approximate `120` SU request
  that a combined Salt1 relaunch would immediately need again. It is therefore
  not enough to make replacement submission demonstrably viable.
- If the replacement is rejected, we lose the running Salt1 continuation and
  gain no combined job.

## Current Salt1 State

Observed from the live Salt1 log:

- Slurm job: `3282992`
- State: running at inspection.
- Latest log time inspected: about `4187.4 s`.
- Retained restart directories include `4187`.
- `system/controlDict` uses `startFrom latestTime`, `writeInterval 1`, and
  `purgeWrite 21`.

Interpretation:

- The case is restartable from the latest retained time if it is later canceled
  or ends.
- `scancel` is not a pause. It would terminate the current MPI job and preserve
  only written outputs.

## Staged Combined Script

Created:

- `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/scripts/run_salt1_nominal_with_rigor_monitors.sbatch`

The script:

1. Runs corrected-Salt preflight into a combined-rigor output directory.
2. Runs corrected-Salt live monitor before Salt1 starts.
3. Runs fixed-mdot 1D replay into the same combined-rigor output directory.
4. Runs thermal-mismatch replay into the same combined-rigor output directory.
5. Starts the 64-rank Salt1 OpenFOAM continuation from the latest available
   `processors64` restart time.

## Relaunch Rule

Use the combined script only when replacement submission is likely to be
accepted. A safe sequence is:

1. Confirm current Salt1 latest retained time and log health.
2. Confirm allocation encumbrance has cleared enough for a 120-hour one-node
   Salt1 job.
3. Only then cancel `3282992`, if it is still running.
4. Submit:

   ```bash
   ssh login3.ls6.tacc.utexas.edu 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/scripts/run_salt1_nominal_with_rigor_monitors.sbatch'
   ```

## Scientific Boundary

The combined lightweight monitor/replay outputs are provenance and diagnostic
support. They do not admit corrected Salt rows, do not make Salt1 closure
evidence, and do not validate empirical friction closures. Formal gates remain
required.
