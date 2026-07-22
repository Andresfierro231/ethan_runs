---
provenance:
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt2_physics_revision_smoke_v1/amx1_physics_revision_smoke_audit/amx1_physics_revision_summary.json
  - ../cfd-modeling-tools/.agent/status/2026-07-21_impl-2026-07-21-fluid-amx1-physics-revision-smoke.md
tags: [forward-model, thermal-modeling, amx1, physics-revision-smoke]
related:
  - ../../../2026-07-21/2026-07-21_amx1_gradient_clipped_smoke_intake/README.md
  - ../../../../../../operational_notes/maps/forward-predictive-model.md
task: AGENT-574
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# AMX1 Physics-Revision Smoke Intake

This package intakes the external Fluid task
`impl-2026-07-21-fluid-amx1-physics-revision-smoke`.

Result: the Salt2 parent-cell AMX1 smoke completed as diagnostic-only evidence.
All root and ledger gates passed, but neither upper/lower vertical parent-cell
`m010` form is ready for a Salt1-Salt4 bounded comparison because both still
worsened `all_rmse_K` and `tp_rmse_K`.

Key files:

- `physics_revision_verdict.csv` records the smoke verdict and no-expansion
  outcome.
- `form_deltas.csv` records AMX1-minus-baseline deltas by parent-cell form.
- `ledger_runtime_summary.csv` records root, ledger, and runtime facts.
- `next_steps.csv` records the next bounded action.
- `source_manifest.csv` records exact source paths used.
- `summary.json` gives machine-readable package state.

Interpretation:

- Parent-cell exchange is a real form change from adjacent-pair diffusion.
- It still worsens the same all-probe/TP metrics, and the closest row is worse
  than the clipped pairwise result.
- The next useful work is not Salt1-Salt4 expansion for this form. Shift effort
  to setup-only wall/test-section/passive-boundary candidates unless new CFD
  structure evidence identifies a better AMX1 source.

Guardrails: no native CFD/OpenFOAM outputs, registry state, scheduler state,
source/property release state, score grid, Salt1-Salt4 expansion, fitting,
model selection, scientific admission, or blocker register were changed by
this intake.
