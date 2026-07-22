---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate/passive_operator_family_smoke.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate/passive_operator_sensitivity_summary.csv
tags: [thermal, passive-h2, runtime-operator, smoke-uq, no-release]
related:
  - .agent/status/2026-07-22_TODO-THERMAL-PASSIVE-H2-RUNTIME-OPERATOR-SMOKE-UQ-GATE-2026-07-22.md
  - .agent/journal/2026-07-22/thermal-passive-h2-runtime-operator-smoke-uq-gate.md
  - imports/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate.json
task: TODO-THERMAL-PASSIVE-H2-RUNTIME-OPERATOR-SMOKE-UQ-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: work_product_readme
status: complete
---
# PASSIVE-H2 Runtime-Operator Smoke/UQ Gate

Decision: `passive_h2_runtime_operator_smoke_uq_gate_diagnostic_no_release_no_admission`.

This package executes a no-leak diagnostic runtime-operator smoke for
`PASSIVE-H2-CAND001` on `salt_2`. It consumes the source-backed setup fields
from the one-train preflight and model-predicted wall-state temperatures from
the train-only smoke. It does not use observed validation temperatures,
realized CFD wallHeatFlux, CFD mdot, Qwall, imposed cooler duty, or a fitted
global multiplier.

The computed passive-operator heat-loss rows are diagnostic only. They are not
a numeric `q_loss` release, source/property release, Qwall release, repair
execution, candidate freeze, coefficient admission, protected score, or final
score.

Key diagnostic numbers:

- nominal passive-operator smoke total:
  `873.272 W`
  (`216.779 W` convective,
  `656.493 W` radiative);
- largest local passive-operator sensitivity:
  `656.493 W`;
- largest existing train-only mdot/TP/TW/heat sensitivities:
  `0.000933618 kg/s`,
  `12.4703 K`,
  `32.628 K`,
  `7.18208 W`.

The direct radiation term is large and the existing `radiation_on` setup-UQ
variant has zero model-output delta. That is a diagnostic caveat, not a
permission to release a radiation-corrected passive heat-loss value.
