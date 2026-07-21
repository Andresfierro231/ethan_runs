---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_amx1_localized_form_smoke_intake/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt2_localized_form_smoke_v1/amx1_localized_smoke_audit/amx1_localized_smoke_summary.json
tags: [forward-model, thermal-modeling, amx1, localized-smoke]
related:
  - .agent/status/2026-07-20_AGENT-569.md
  - imports/2026-07-20_amx1_localized_form_smoke_intake.json
task: AGENT-569
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# AMX1 Localized-Form Smoke Intake

## Attempted

- Claimed AGENT-569 for the Ethan intake side and a separate Fluid row for the
  localized-form smoke.
- Ran Salt2 only with disabled baseline, broad-control AMX1, and three
  single-parent localized variants at multiplier `0.05`.
- Summarized the Fluid audit into
  `work_products/2026-07/2026-07-20/2026-07-20_amx1_localized_form_smoke_intake/`.

## Observed

- Fluid manifest: `5/5` rows completed `ok`.
- Audit result: `localized_smoke_complete_diagnostic_only`.
- Root/ledger gates passed for all AMX1 variants.
- No form passed the progression criterion for a separate Salt1-Salt4 bounded
  comparison.
- `upper_vertical_only` and `lower_vertical_only` were closest: both improved
  mdot/velocity and TW metrics, but both still worsened all-probe and TP RMSE.
- Runtime: total campaign `528.803825 s`, solve time `503.636152 s`, max
  scenario duration `112.448520 s`.

## Inferred

Localization changes the AMX1 failure mode in a useful way. The upper/lower
vertical-only forms no longer worsen TW metrics, unlike the broad and
test-section-only forms, but they still leave TP/all-probe regressions. That is
not enough to unlock `predictive-wall-test-section-submodels`, but it narrows
the next AMX1 search to lower multiplier or gradient-clipped upper/lower
vertical exchange.

## Caveats

- This was a form smoke, not a score grid or model-selection run.
- Only Salt2 was run; Salt1-Salt4 expansion was intentionally deferred.
- Validation temperatures were diagnostic targets only and not runtime inputs.

## Next Useful Actions

1. Run a second Salt2-only smoke with lower multipliers for upper/lower
   vertical-only forms.
2. If multiplier reduction still worsens TP/all-probe metrics, implement a
   disabled-by-default gradient-clipped AMX1 mode.
3. Run Salt1-Salt4 only after one Salt2 form keeps mdot, TP, TW, and all-probe
   core deltas nonpositive while preserving root and ledger gates.
