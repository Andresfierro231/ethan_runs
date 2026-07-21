---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_amx1_gradient_clipped_smoke_intake/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt2_gradient_clipped_smoke_v1/amx1_gradient_clipped_smoke_audit/amx1_gradient_clipped_summary.json
tags: [forward-model, thermal-modeling, amx1, gradient-clipped-smoke]
related:
  - .agent/status/2026-07-21_AGENT-573.md
  - imports/2026-07-21_amx1_gradient_clipped_smoke_intake.json
task: AGENT-573
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# AMX1 Gradient-Clipped Smoke Intake

## Attempted

- Claimed AGENT-573 for Ethan intake and
  `impl-2026-07-21-fluid-amx1-gradient-clipped-smoke` for the Fluid run.
- Added and ran Salt2-only `amx1_salt2_gradient_clipped_smoke_v1` with one
  disabled baseline plus upper/lower vertical-only AMX1 `m010` rows using a
  fixed `0.05 K` pair-gradient cap.
- Summarized the Fluid audit into
  `work_products/2026-07/2026-07-21/2026-07-21_amx1_gradient_clipped_smoke_intake/`.

## Observed

- Fluid manifest: `3/3` rows completed `ok`.
- Audit decision: `gradient_clipped_smoke_complete_diagnostic_only`.
- Root/ledger gates passed for both AMX1 rows.
- No form passed the progression criterion for a separate Salt1-Salt4 bounded
  comparison.
- Both rows improved mdot/velocity and TW metrics, but still worsened
  `all_rmse_K` and `tp_rmse_K`.
- Closest form: `upper_vertical_only_m010_clip0050`, with
  `max_positive_core_delta=0.00005769407099620594 K`.
- Runtime: total campaign `303.77009 s`, solve time `284.528675 s`, max
  scenario duration `113.542427 s`.

## Inferred

The gradient cap reduces the all-probe/TP regression magnitude by roughly a
factor of three relative to unclipped `upper_vertical_only_m010`, but it does
not reverse the sign. That argues against spending the next bounded run on
weaker variants of the same local diffusive exchange. The next useful AMX1
work is a physical-form revision, or returning effort to the
wall/test-section/passive-boundary submodel blocker.

## Caveats

- This was a Salt2 diagnostic smoke, not a score grid or model-selection run.
- Salt1-Salt4 expansion was intentionally deferred.
- Diagnostic temperature targets were not used as runtime inputs.

## Next Useful Actions

1. Do not run Salt1-Salt4 for the current clipped AMX1 form.
2. If continuing AMX1, revise the physical placement or source term rather than
   only reducing exchange strength.
3. In parallel, prioritize a setup-only wall/test-section/passive-boundary
   candidate because AMX1 has now produced repeated wrong-sign TP/all-probe
   deltas under broad, localized, lower-multiplier, and clipped forms.
