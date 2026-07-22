# Corrected Salt Q Gate 3280969 Review

Date: `2026-07-09`
Task: `AGENT-237`

## 2026-07-13 Coordinator Correction

The original conclusion that `too_short` makes every row closure-fit
inadmissible is superseded. Current policy is that a converged/stationary
terminal-window Salt-Q perturbation row is closure-fit admissible. The old
post-restart-advance threshold is context only for otherwise converged rows.
Rows with failed/cancelled launch evidence or no usable terminal window remain
repair-first.

## Sources

- Gate scheduler state: `sacct -j 3280969` reported `COMPLETED`, exit `0:0`, from `2026-07-09T12:22:28` to `2026-07-09T12:23:43`.
- Gate logs:
  - `tmp/2026-07-06_overnight_postprocess_jobs/slurm-saltq_gate_after-3280969.out`
  - `tmp/2026-07-06_overnight_postprocess_jobs/slurm-saltq_gate_after-3280969.err`
- Completed gate outputs:
  - `work_products/2026-07-06_overnight_postprocess_jobs/corrected_salt_after_3275448_3275449_3275560/corrected_salt_solver_audit_summary.csv`
  - `work_products/2026-07-06_overnight_postprocess_jobs/corrected_salt_after_3275448_3275449_3275560/run_status/run_status_inventory.csv`
- Earlier comparison baseline:
  - `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/tables/corrected_salt_status_summary.csv`

## Gate Result

Under the July 13 correction, converged/stationary Salt-Q perturbation rows from
this gate are closure-fit admissible even if the older run-status inventory
reported `operating_point_verdict=too_short`.

The one-line collector summary is necessary but not sufficient for admission:
it reports `direction ok=14/14`, `preflight bad ok count=0`, and
`special scrutiny flags=1`, but the same package README states this is only a
direction check. The formal operating-point gate is the authority for closure
admission, and it did not return `requalified` for any row.

## Row Classes

- `admissible`: 0 rows.
- `partial_requires_extended_continuation`: 11 rows.
  These rows have correct mdot direction, no special scrutiny flag, and a full
  300 s late monitor window, but they remain document-only because the formal
  operating-point gate is `too_short`.
- `excluded_rerun` / `excluded_rebuild`: 3 rows.
  Salt3 +5Q and +10Q have only about 20-21 s of post-restart evidence from the
  cancelled/superseded high-Q attempt. Salt1 +10Q ended after about 254 s via
  the convergence-monitor path and has no complete 300 s late window.

Detailed row verdicts are in `row_verdicts.csv`.

## Timeout Interpretation

The parent jobs timed out at the scheduler level (`3275448`, `3275449`, and
`3275560`), but timeout alone does not decide admission. The useful distinction
is:

- Timed out with usable partial window: Salt1 -10Q; all Salt2 rows; Salt3 -10Q
  and -5Q; all Salt4 rows. These can support status plots and resubmit planning
  only.
- Timed out/cancelled without usable partial window: Salt1 +10Q, Salt3 +5Q, and
  Salt3 +10Q. These should not be used even as partial operating-point evidence
  beyond explaining why they need rerun/rebuild.

The gate uses `tau_thermal=5000 s` and `min_tau_advance=3`, so a row needs
about 15,000 s post-restart advance before it can clear the `too_short` branch.
The staged corrected-Q cases target only about 6,000 s post-restart advance;
therefore a simple rerun to the current `endTime` would still be insufficient
under the current formal gate policy.

## Resubmit List

See `resubmit_list.csv`.

Recommended ordering:

1. Extend all four Salt2 rows first; these are the cleanest and most directly
   useful range-expansion candidates.
2. Extend Salt3 low-Q and Salt4 rows next; they also have clean partial windows.
3. Treat Salt1 -10Q as coordinator-review only until the Salt1 nominal-reference
   policy is resolved.
4. Rerun or rebuild Salt3 +5Q and +10Q from the corrected restart; they do not
   have usable windows.
5. Fix the Salt1 +10Q stop/reference policy before any rerun or continuation.

## Closure Boundary

Do not add any of these rows to F4/F5/F6/T13 closure fits, model-form bakeoffs,
or publication-grade validation tables until a future formal gate returns
`operating_point_verdict=requalified` for the specific row.
