# Corrected Salt Q Minimal Continuation Plan

## Plan

Built a no-submit continuation/resubmit plan from the completed `3280969` gate
audit and corrected-Q campaign submission docs.

Decision:

- No row is admitted now because `3280969` returned
  `operating_point_verdict=too_short` and `closure_fit_admissible=no` for all
  corrected-Q rows.
- Do not bulk-resubmit the corrected Salt Q campaign and do not use
  `scripts/submit_corrected_jobs.sh` as-is.
- Minimal first continuation wave is only:
  - `salt2_jin_lo10q_corrected`
  - `salt2_jin_hi10q_corrected`
- Salt4 +/-10Q is deferred until wave 1 admits or validates the continuation
  setup.
- Salt2/Salt4 +/-5Q midpoint rows are deferred until nonlinearity/local-slope
  support is needed.
- Salt3 low-Q rows are deferred as asymmetric support because Salt3 high-Q rows
  failed/cancelled.
- Salt1 -10Q is held pending Salt1 reference/admission policy.
- Salt1 +10Q and Salt3 +5Q/+10Q require investigation or repair before any
  resubmit.

Outputs:

- `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_minimal_continuation_plan/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_minimal_continuation_plan/minimal_continuation_plan.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_minimal_continuation_plan/no_submit_checklist.md`

No corrected Salt case trees, scheduler state, native solver outputs, gate
outputs, or closure-fit tables were modified. All future admitted corrected-Q
rows remain labeled as sensitivity/correlation-support, not nominal baselines.
