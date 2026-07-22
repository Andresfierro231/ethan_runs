---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke/case_corrected_radiation_summary.csv
tags: [thermal, passive-h2, multi-train, corrected-radiation, diagnostic]
related:
  - .agent/status/2026-07-22_TODO-THERMAL-PASSIVE-H2-MULTI-TRAIN-CORRECTED-RADIATION-SMOKE-2026-07-22.md
  - .agent/journal/2026-07-22/thermal-passive-h2-multi-train-corrected-radiation-smoke.md
  - imports/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke.json
task: TODO-THERMAL-PASSIVE-H2-MULTI-TRAIN-CORRECTED-RADIATION-SMOKE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Multi-Train Corrected Radiation Smoke

Decision: `passive_h2_multi_train_corrected_radiation_smoke_supports_development_no_admission`.

This package extends the corrected outer-insulation-surface PASSIVE-H2 operator
to Salt2/Salt3/Salt4 using existing train-only setup-UQ outputs and
case-specific passive external-boundary setup rows.

The result supports continued train-context testing: corrected passive totals
span `38.6073` to `44.6771` W, far below
the prior naive inner-wall radiation basis. This is still diagnostic only: no
fit, protected score, source/property release, Qwall release, numeric q-loss
release, candidate freeze, or final score was made.
