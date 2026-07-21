# Corrected Salt Q Convergence/Resubmit Recommendations

## Review

Strengthened the existing AGENT-238 minimal continuation plan with a stricter
row-level interpretation of terminal-window convergence versus formal closure
admission.

Findings:

- No corrected-Q perturbation row is fully admitted for F5/Ri or F6 refit.
- 11 rows are terminal-window stationary but under-advanced. They are useful
  for planning/status only and still require continuation plus formal re-gate.
- 3 rows are not accepted as terminal windows:
  - `salt1_jin_hi10q_corrected`
  - `salt3_jin_hi5q_corrected`
  - `salt3_jin_hi10q_corrected`
- The only recommended first-wave continuation rows are:
  - `salt2_jin_lo10q_corrected`
  - `salt2_jin_hi10q_corrected`
- Salt2/Salt4 midpoints, Salt4 +/-10Q, Salt3 low-Q rows, and Salt1 -10Q remain
  deferred or policy-held.
- Salt1 +10Q and Salt3 high-Q rows require investigation or repair before any
  resubmit.

Outputs:

- Updated `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_minimal_continuation_plan/README.md`
- Added `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_minimal_continuation_plan/convergence_resubmit_recommendations.csv`

No scheduler action, corrected Salt case-tree mutation, native solver-output
mutation, or closure-fit table update was performed. All rows remain labeled
as sensitivity/correlation-support if future formal gate evidence admits them.
