---
provenance:
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/amx1_salt1_4_bounded_nominal_v1/amx1_bounded_nominal_audit/amx1_bounded_summary.json
  - ../cfd-modeling-tools/.agent/status/2026-07-20_impl-2026-07-20-fluid-amx1-salt1-4-bounded-comparison.md
tags: [forward-model, thermal-modeling, amx1, bounded-comparison]
related:
  - ../../../2026-07-20/2026-07-20_amx1_salt2_smoke_intake/README.md
  - ../../../../../../operational_notes/maps/forward-predictive-model.md
task: AGENT-568
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# AMX1 Salt1-Salt4 Bounded Comparison Intake

This package intakes the external Fluid task
`impl-2026-07-20-fluid-amx1-salt1-4-bounded-comparison`.

Result: the bounded comparison completed as diagnostic-only evidence. The AMX1
form survives finite-root and conservative-ledger gates across Salt1-Salt4, but
it is not scorecard-ready because all temperature RMSE families worsen
slightly while mdot and velocity errors improve.

Key files:

- `bounded_verdict.csv` records the root, ledger, runtime, and no-admission
  verdict.
- `case_metric_deltas.csv` records paired AMX1-minus-baseline deltas.
- `ledger_root_runtime_summary.csv` records per-case root/ledger facts and
  runtime.
- `next_steps.csv` records the next bounded actions.
- `source_manifest.csv` records the exact Fluid inputs and outputs used here.
- `summary.json` gives a machine-readable intake summary.

Interpretation:

- AMX1 should remain active as a numerically valid hook.
- The current uniform adjacent-segment diffusion form should not advance to a
  score grid or admission path.
- The next useful study should revise the form: direction-selective, localized,
  or boundary-coupled axial exchange that can improve mdot without pushing TP
  and TW probes in the wrong direction.

Guardrails: no native CFD/OpenFOAM outputs, registry state, scheduler state,
source/property release state, score grid, fitting, model selection, scientific
admission, or blocker register were changed by this intake.
