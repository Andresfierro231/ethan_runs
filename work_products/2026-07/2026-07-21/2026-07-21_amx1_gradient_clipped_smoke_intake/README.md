---
provenance:
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt2_gradient_clipped_smoke_v1/amx1_gradient_clipped_smoke_audit/amx1_gradient_clipped_summary.json
  - ../cfd-modeling-tools/.agent/status/2026-07-21_impl-2026-07-21-fluid-amx1-gradient-clipped-smoke.md
tags: [forward-model, thermal-modeling, amx1, gradient-clipped-smoke]
related:
  - ../../../2026-07-20/2026-07-20_amx1_lower_multiplier_smoke_intake/README.md
  - ../../../../../../operational_notes/maps/forward-predictive-model.md
task: AGENT-573
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# AMX1 Gradient-Clipped Smoke Intake

This package intakes the external Fluid task
`impl-2026-07-21-fluid-amx1-gradient-clipped-smoke`.

Result: the Salt2 gradient-clipped smoke completed as diagnostic-only evidence.
All root and ledger gates passed, but neither upper/lower vertical-only clipped
`m010` form is ready for a Salt1-Salt4 bounded comparison because both still
worsened `all_rmse_K` and `tp_rmse_K`.

Key files:

- `gradient_clipped_verdict.csv` records the smoke verdict and no-expansion
  outcome.
- `form_deltas.csv` records AMX1-minus-baseline deltas by clipped form.
- `ledger_runtime_summary.csv` records root, ledger, and runtime facts.
- `next_steps.csv` records the next bounded action.
- `source_manifest.csv` records exact source paths used.
- `summary.json` gives machine-readable package state.

Interpretation:

- The cap reduced the prior TP/all-probe regression magnitude but did not
  reverse its sign.
- `upper_vertical_only_m010_clip0050` is closest, with max positive core delta
  `0.00005769407099620594 K`.
- The next useful work is not Salt1-Salt4 expansion for this form. Either
  revise AMX1 physics beyond strength limiting or focus on the
  wall/test-section/passive-boundary submodel blocker.

Guardrails: no native CFD/OpenFOAM outputs, registry state, scheduler state,
source/property release state, score grid, Salt1-Salt4 expansion, fitting,
model selection, scientific admission, or blocker register were changed by
this intake.
