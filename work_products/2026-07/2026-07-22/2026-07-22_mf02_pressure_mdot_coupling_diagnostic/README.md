---
provenance:
  generated_by: tools/analyze/build_mf02_pressure_mdot_coupling_diagnostic.py
  task_id: TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22
  generated_at_utc: 2026-07-22T13:28:51.811248+00:00
task: TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22
tags:
  - MF02
  - pressure
  - mdot
  - diagnostic
related:
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/section_effective_pressure_scorecard.csv
  - work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/no_fit_performance_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate/summary.json
---

# MF02 Pressure-Mdot Coupling Diagnostic

## Decision

MF02 is useful as a diagnostic scale estimate only. The lower-right pressure
rise is hydrostatic/recovery/section-effective evidence, not negative loss and
not component-K/F6 evidence.

Across the three available lower-right rows, the signed residual magnitude is
`0.040853145189147615%` to `0.06058295828566344%`
of gross static pressure rise. A gross-scale quadratic mdot estimate would be
only `0.03029147914283172%` at most, but this is not a
predictive mdot correction because the residual is not an admitted loop-loss
term.

## Guardrails

No F6 fit, component K, cluster K, clipped K, hidden/global multiplier, mixed
basis promotion, solver/sampler launch, fitting, model selection, source/property
release, admission, registry mutation, native-output mutation, or S11/S15/S6
trigger was performed.
