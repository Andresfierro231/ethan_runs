---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/forward_v0_hydraulic_residuals.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/summary.json
tags: [forward-model, predictive-1d, hydraulics, h1-proxy, scorecard]
related:
  - .agent/status/2026-07-14_AGENT-310.md
  - imports/2026-07-14_predictive_h1_hydraulic_scorecard.json
  - operational_notes/maps/friction-closures.md
  - operational_notes/maps/pressure-and-momentum-budget.md
task: AGENT-310
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Predictive H1 Hydraulic Scorecard

## Observed Output

AGENT-310 built `work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/` from existing H1 proxy, hydraulic gate, validation split, and named-loss/reset evidence.

For the main `F1_heater_only` lane, H1 reduced mean mdot error vs CFD from `0.0054775 kg/s` (`36.371%`) to `0.0021441666666666666 kg/s` (`14.419%` mean row percent), a `60.288%` reduction. The row-level scorecard keeps `salt_2` as training residual only, `salt_3` as validation diagnostic, and `salt_4` as holdout diagnostic.

The H1 run remains an aggregate fixed-K proxy: it used Salt2 finite fit-target branch-apparent `K_local` rows only. It did not fit thermal terms and did not edit external Fluid.

## Inferred Interpretation

H1 improves mdot enough to unblock a forward-v1 scorecard refresh as diagnostic/proxy hydraulic evidence. It does not admit a final localized H1 closure, because current Fluid support only exercised an aggregate `MinorLosses` fixed-K proxy and all H1 rows still overpredict CFD mdot.

The term-boundary ledger is the guardrail against hiding errors: straight pressure-gradient friction, straight-section named loss, component-K absence, cluster K, branch-apparent K, reset/development, momentum-corrected profile/debuoying, and recirculation diagnostics are reported separately.

## Next Actions

1. Reopen the forward-v1 scorecard row using AGENT-310 as the hydraulic diagnostic input.
2. If a final hydraulic closure is needed, create a separate Fluid/API task for localized named-loss and reset metadata; keep `../cfd-modeling-tools/**` read-only until claimed.
3. Do not fit thermal corrections against the remaining mdot residual; the H1 scorecard is hydraulic-only.

## Validation

- `python3.11 -m py_compile tools/analyze/build_predictive_h1_hydraulic_scorecard.py tools/analyze/test_predictive_h1_hydraulic_scorecard.py`
- `python3.11 -m unittest tools.analyze.test_predictive_h1_hydraulic_scorecard`
- `python3.11 tools/analyze/build_predictive_h1_hydraulic_scorecard.py`

Generated index refresh was intentionally deferred because active AGENT-309 owns `.agent/STATE.md`, `.agent/catalog.json`, `.agent/catalog.csv`, and `.agent/BLOCKERS.md`.
