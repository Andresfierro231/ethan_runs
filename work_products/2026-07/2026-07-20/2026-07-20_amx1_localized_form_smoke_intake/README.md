---
provenance:
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt2_localized_form_smoke_v1/amx1_localized_smoke_audit/amx1_localized_smoke_summary.json
  - ../cfd-modeling-tools/.agent/status/2026-07-20_impl-2026-07-20-fluid-amx1-localized-form-smoke.md
tags: [forward-model, thermal-modeling, amx1, localized-smoke]
related:
  - ../../../2026-07-20/2026-07-20_amx1_salt1_4_bounded_comparison_intake/README.md
  - ../../../../../../operational_notes/maps/forward-predictive-model.md
task: AGENT-569
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# AMX1 Localized-Form Smoke Intake

This package intakes the external Fluid task
`impl-2026-07-20-fluid-amx1-localized-form-smoke`.

Result: the Salt2 localized-form smoke completed as diagnostic-only evidence.
All root and ledger gates passed, but no localized form is ready for a
Salt1-Salt4 bounded comparison because every form still worsened all-probe RMSE
and/or TP RMSE.

Key files:

- `localized_verdict.csv` records the smoke verdict and no-expansion outcome.
- `form_deltas.csv` records AMX1-minus-baseline deltas by localized form.
- `ledger_runtime_summary.csv` records root, ledger, and runtime facts.
- `next_steps.csv` records the next bounded action.
- `source_manifest.csv` records exact source paths used.
- `summary.json` gives machine-readable package state.

Interpretation:

- Localization improved the failure mode but did not unlock the blocker.
- `upper_vertical_only` and `lower_vertical_only` are the closest forms: they
  improve mdot, velocity, TW RMSE, and TW-without-TW10 RMSE, but still worsen
  all-probe and TP RMSE.
- The next useful AMX1 study should stay Salt2-only and narrow around those two
  forms with lower multiplier or gradient-clipped exchange before any
  Salt1-Salt4 rerun.

Guardrails: no native CFD/OpenFOAM outputs, registry state, scheduler state,
source/property release state, score grid, Salt1-Salt4 expansion, fitting,
model selection, scientific admission, or blocker register were changed by
this intake.
