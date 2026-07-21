# Time-Series Uncertainty Digest Sbatch

Date: `2026-07-10`
Task: `AGENT-256`
Role: Coordinator / Implementer / Tester / Writer

## Prompt

The user asked to submit the time-series uncertainty digest as an `sbatch` job
for runs that are done and no longer running, and to confirm whether any jobs
are running in the background of the current node.

## Background Process Check

Current node:

```text
c318-008.ls6.tacc.utexas.edu
```

`tmux ls` showed:

- `work`: attached multi-agent session.
- `salt4_attach_3288671`: active launcher session.

`ps -f -u andresfierro231` showed an `srun --jobid=3288671` launcher process
under the Salt4 attach session. Therefore this node is not background-clean.
The background activity is intentional AGENT-253 corrected-Q attach work.

## Implementation

Added `tools/analyze/build_time_series_uncertainty_digest.py`.

The builder consumes:

- `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv`

It excludes live/active case slugs associated with:

- Salt1 nominal continuation job `3282992`;
- selected corrected-Q continuation job `3288671`.

It writes:

- `uncertainty_digest_all_terminal_cases.csv`
- `uncertainty_digest_admitted_mainline_salt234.csv`
- `presentation_uncertainty_summary_salt234.csv`
- `excluded_live_or_active_cases.csv`
- `summary.json`
- `README.md`

## Submission

Submission is via:

```bash
sbatch work_products/2026-07/2026-07-10/2026-07-10_time_series_uncertainty_digest_sbatch/scripts/run_time_series_uncertainty_digest.sbatch
```

The job is intentionally small and uses the `development` partition with a
20-minute wall limit.

Submitted from `login3`:

```text
Submitted batch job 3289056
```

Immediate scheduler/accounting check:

```text
3289056|ts_unc_digest|PENDING|0:00|20:00|1|(Priority)
3289056|ts_unc_digest|PENDING|0:0|00:00:00|Unknown|Unknown|00:20:00|None assigned
```

## Validation Before Submission

- Python compile passed.
- `bash -n` on the sbatch wrapper passed.
- Import manifest JSON parsed.
- Local smoke wrote `/tmp/agent256_uncertainty_digest_smoke`.

Smoke counts:

- input rows: `415`;
- terminal/non-live digest rows: `379`;
- mainline Salt2/3/4 rows: `27`;
- presentation Salt2/3/4 case rows: `3`;
- excluded live/active rows: `36`.

## Final Result

Final accounting:

```text
3289056|ts_unc_digest|COMPLETED|0:0|00:00:02|2026-07-10T17:37:19|2026-07-10T17:37:21|00:20:00|c307-006
```

Final package:

- `work_products/2026-07/2026-07-10/2026-07-10_time_series_uncertainty_digest_sbatch/README.md`
- `work_products/2026-07/2026-07-10/2026-07-10_time_series_uncertainty_digest_sbatch/summary.json`
- `work_products/2026-07/2026-07-10/2026-07-10_time_series_uncertainty_digest_sbatch/uncertainty_digest_all_terminal_cases.csv`
- `work_products/2026-07/2026-07-10/2026-07-10_time_series_uncertainty_digest_sbatch/uncertainty_digest_admitted_mainline_salt234.csv`
- `work_products/2026-07/2026-07-10/2026-07-10_time_series_uncertainty_digest_sbatch/presentation_uncertainty_summary_salt234.csv`
- `work_products/2026-07/2026-07-10/2026-07-10_time_series_uncertainty_digest_sbatch/excluded_live_or_active_cases.csv`

Final counts matched the smoke:

- terminal/non-live digest rows: `379`;
- excluded live/active rows: `36`;
- admitted-mainline Salt2/3/4 series rows: `27`;
- admitted-mainline Salt2/3/4 presentation rows: `3`.
