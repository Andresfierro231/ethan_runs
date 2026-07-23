---
provenance:
  generated_by: tools/analyze/build_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest.py
  task_id: TODO-PASSIVE-H2-SALT14-PM5-VALSALT2-DIAGNOSTIC-TRAINTEST-2026-07-22
tags: [journal, PASSIVE-H2, predictive-model]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt14_pm5_valsalt2_diagnostic_traintest/summary.json
task: TODO-PASSIVE-H2-SALT14-PM5-VALSALT2-DIAGNOSTIC-TRAINTEST-2026-07-22
---
# PASSIVE-H2 Salt1-4 / PM5 / val_salt2 Diagnostic Train-Test

Task: `TODO-PASSIVE-H2-SALT14-PM5-VALSALT2-DIAGNOSTIC-TRAINTEST-2026-07-22`

## Attempted

I assembled the requested Salt1-4 training and Salt2 +/-5Q plus `val_salt2`
testing contract from the canonical split policy, final scorecard shell,
completed PASSIVE-H2 prototype/smoke packages, PM5 target package, and
`val_salt2` external target package.

## Observed

- Canonical training rows are Salt1-4 nominal.
- Completed PASSIVE-H2 runtime/prediction evidence exists for Salt2-4 only.
- Salt2 +/-5Q and `val_salt2` target evidence exists, but no admitted frozen
  PASSIVE-H2 prediction artifact exists for those rows.
- The final scorecard shell keeps fit/model selection closed under the current
  source/property policy.

## Inferred

The requested train/test cannot be claimed as an admitted predictive score yet.
The rigorous next step is not to reduce the training set to Salt2-4, because
that would no longer be the requested Salt1-4 fit and would weaken the split
contract.

## Next Useful Actions

1. Generate Salt1 PASSIVE-H2 setup-only runtime prediction evidence.
2. Resolve or explicitly waive source/property release only in a diagnostic
   package.
3. Freeze coefficients from Salt1-4 before creating blind PM5 and `val_salt2`
   PASSIVE-H2 predictions.
4. Score holdout and external-test rows separately with no retuning.

Decision recorded as `passive_h2_salt14_pm5_valsalt2_requested_traintest_blocked_no_fit_no_score`.
