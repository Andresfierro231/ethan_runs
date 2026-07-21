# CFD Steady-State Continuation Table

Date: `2026-07-09`
Task ID: `AGENT-246`
Role: Coordinator / Writer

## Request

Prepare a table showing which CFD runs are at steady state and which need to be
continued.

## Evidence Used

- AGENT-244 time-series steady-state summary:
  `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv`
- Corrected Salt Q gate review:
  `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_gate_3280969_review/row_verdicts.csv`
- Corrected Salt Q continuation recommendations:
  `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_minimal_continuation_plan/convergence_resubmit_recommendations.csv`
- Salt1 nominal live admission memo and current scheduler/log check.

## Observed Output

- AGENT-244 covers `47` unique cases.
- The compact operational table has `22` rows.
- Salt1 nominal job `3282992` remained `RUNNING` at check and had advanced to
  about `Time = 5040.975s`.

## Decision

Operationally, continue only:

1. live Salt1 nominal `3282992` until terminal gate evidence exists;
2. corrected-Q Salt2 -10Q/+10Q if corrected-Q continuation is authorized.

Salt4 nominal is steady and does not need continuation now. Salt2/3 nominal are
hydraulically steady but carry thermal `total_Q` drift caveats. Corrected-Q
midpoint, Salt4 bracket, and Salt3 low-Q rows are deferred. Salt3 high-Q and
Salt1 +10Q corrected rows are repair-first.

No solver outputs were modified.
