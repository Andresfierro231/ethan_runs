---
provenance:
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt2_lower_multiplier_smoke_v2/amx1_lower_multiplier_smoke_audit/amx1_lower_multiplier_summary.json
  - ../cfd-modeling-tools/.agent/status/2026-07-20_impl-2026-07-20-fluid-amx1-lower-multiplier-smoke.md
tags: [forward-model, thermal-modeling, amx1, lower-multiplier-smoke]
related:
  - ../../../2026-07-20/2026-07-20_amx1_localized_form_smoke_intake/README.md
  - ../../../../../../operational_notes/maps/forward-predictive-model.md
task: AGENT-572
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# AMX1 Lower-Multiplier Smoke Intake

This package intakes the external Fluid task
`impl-2026-07-20-fluid-amx1-lower-multiplier-smoke`.

Result: the Salt2 lower-multiplier smoke completed as diagnostic-only
evidence. All root and ledger gates passed, but no upper/lower vertical-only
multiplier is ready for a Salt1-Salt4 bounded comparison because every form
still worsened `all_rmse_K` and `tp_rmse_K`.

Key files:

- `lower_multiplier_verdict.csv` records the smoke verdict and no-expansion
  outcome.
- `form_deltas.csv` records AMX1-minus-baseline deltas by form and multiplier.
- `ledger_runtime_summary.csv` records root, ledger, and runtime facts.
- `next_steps.csv` records the next bounded action.
- `source_manifest.csv` records exact source paths used.
- `summary.json` gives machine-readable package state.

Interpretation:

- Lower multiplier shrinks the prior TP/all-probe regressions but does not
  reverse their sign.
- `upper_vertical_only_m010` is closest, with max positive core delta
  `0.00019863866604197256 K`.
- The next useful AMX1 study is a disabled-by-default gradient-clipped localized
  exchange smoke, still Salt2-only at first.

Guardrails: no native CFD/OpenFOAM outputs, registry state, scheduler state,
source/property release state, score grid, Salt1-Salt4 expansion, fitting,
model selection, scientific admission, or blocker register were changed by
this intake.
