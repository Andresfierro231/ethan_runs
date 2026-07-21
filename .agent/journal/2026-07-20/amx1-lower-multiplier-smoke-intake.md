---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_amx1_lower_multiplier_smoke_intake/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt2_lower_multiplier_smoke_v2/amx1_lower_multiplier_smoke_audit/amx1_lower_multiplier_summary.json
tags: [forward-model, thermal-modeling, amx1, lower-multiplier-smoke]
related:
  - .agent/status/2026-07-20_AGENT-572.md
  - imports/2026-07-20_amx1_lower_multiplier_smoke_intake.json
task: AGENT-572
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# AMX1 Lower-Multiplier Smoke Intake

## Attempted

- Claimed AGENT-572 for Ethan intake and
  `impl-2026-07-20-fluid-amx1-lower-multiplier-smoke` for the Fluid run.
- Added and ran Salt2-only `amx1_salt2_lower_multiplier_smoke_v2` with one
  disabled baseline plus upper/lower vertical-only AMX1 rows at `0.01`,
  `0.02`, and `0.035`.
- Summarized the Fluid audit into
  `work_products/2026-07/2026-07-20/2026-07-20_amx1_lower_multiplier_smoke_intake/`.

## Observed

- Fluid manifest: `7/7` rows completed `ok`.
- Audit decision: `lower_multiplier_smoke_complete_diagnostic_only`.
- Root/ledger gates passed for all AMX1 rows.
- No form passed the progression criterion for a separate Salt1-Salt4 bounded
  comparison.
- Every AMX1 row improved mdot/velocity and TW metrics, but still worsened
  `all_rmse_K` and `tp_rmse_K`.
- Closest form: `upper_vertical_only_m010`, with
  `max_positive_core_delta=0.00019863866604197256 K`.
- Runtime: total campaign `755.5354629999999 s`, solve time `731.341217 s`,
  max scenario duration `113.182292 s`.

## Inferred

Lowering the AMX1 multiplier shrinks the Salt2 all-probe and TP regressions
almost linearly, but it does not change their sign. This narrows the useful
line of work: the next AMX1 form should add a local gradient/sign clip or
equivalent bounded limiter before any Salt1-Salt4 expansion.

## Caveats

- This was a Salt2 diagnostic smoke, not a score grid or model-selection run.
- Salt1-Salt4 expansion was intentionally deferred.
- Diagnostic temperature targets were not used as runtime inputs.

## Next Useful Actions

1. Implement a disabled-by-default gradient-clipped AMX1 localized exchange
   mode.
2. Smoke only Salt2 first, starting from upper/lower vertical-only `m010`.
3. Run Salt1-Salt4 only after one Salt2 form keeps mdot, TP, TW, and all-probe
   core deltas nonpositive while preserving root and ledger gates.
