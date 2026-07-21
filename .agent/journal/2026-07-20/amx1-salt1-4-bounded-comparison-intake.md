---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_amx1_salt1_4_bounded_comparison_intake/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt1_4_bounded_nominal_v1/amx1_bounded_nominal_audit/amx1_bounded_summary.json
tags: [forward-model, thermal-modeling, amx1, bounded-comparison]
related:
  - .agent/status/2026-07-20_AGENT-568.md
  - imports/2026-07-20_amx1_salt1_4_bounded_comparison_intake.json
task: AGENT-568
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# AMX1 Salt1-Salt4 Bounded Comparison Intake

## Attempted

- Claimed AGENT-568 for the Ethan intake side and a separate Fluid row for the
  reduced-order campaign/audit implementation.
- Added the Fluid `amx1_salt1_4_bounded_nominal_v1` campaign: Salt1-Salt4,
  disabled baseline plus one AMX1 row at multiplier `0.05`.
- Ran the Fluid campaign and audit, then summarized the results into
  `work_products/2026-07/2026-07-20/2026-07-20_amx1_salt1_4_bounded_comparison_intake/`.

## Observed

- Fluid manifest: `8/8` rows completed `ok`.
- Audit result: `bounded_comparison_complete_diagnostic_only`.
- Root/ledger gates passed: all pressure and temperature roots were accepted
  and bracketed; four AMX1 rows had nonzero conservative ledgers.
- AMX1 active segments: `46` per Salt case.
- Runtime: total campaign `753.931202 s`, solve time `726.891243 s`, max
  scenario duration `477.721667 s`.
- Paired deltas: mdot and velocity absolute errors decreased in every Salt
  case, but all temperature RMSE families increased in every Salt case.

## Inferred

The current AMX1 implementation is numerically viable but not predictive enough
to unlock `predictive-wall-test-section-submodels`. It changes the hydraulic
closure in a helpful direction while nudging TP/TW and all-probe temperatures
slightly away from the validation targets. That combination supports keeping
the hook but revising its form before any score-grid or admission work.

## Caveats

- This was one low multiplier only, not a tuning or model-selection pass.
- The Fluid audit used validation metrics only for diagnostic comparison after
  solving; measured temperatures were not runtime inputs.
- No source/property release was attempted.

## Next Useful Actions

1. Try a localized AMX1 smoke: test-section-only, upper-upcomer-only, or
   temperature-gradient-clipped exchange.
2. Require Salt2 smoke roots and ledgers before rerunning Salt1-Salt4.
3. Promote only a revised form that improves or preserves TP/TW/all-probe
   metrics while retaining mdot gains and runtime bounds.
