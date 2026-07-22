---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/next_use_gate.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heated_incline_tw4_tw6_local_audit/failure_classification.csv
tags: [fluid, setup-known-source, heater-source, train-only]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_heated_incline_tw4_tw6_local_audit
task: TODO-FLUID-SETUP-KNOWN-SOURCE-SINK-RUNTIME-CONTRACT-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
---
# Setup-Known Source/Sink Runtime Contract

This package releases a train-only runtime contract for the lower-leg heater
source lane using the existing Fluid `heater_source_mode=tw4_to_tp3_three_span`
capability and recovered setup-known Salt2 heater power.

Result: `setup_known_lower_leg_heater_contract_ready_for_train_only_residual_decomposition`.

- contract rows: `3`
- runtime-admitted rows: `0`
- source/property release rows: `0`
- external Fluid mutation: `false`

Next action is the separately claimed train-only residual decomposition row.
