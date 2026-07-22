---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_thermal_accounting_traceability_evidence_packet/thermal_accounting_traceability_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_thermal_accounting_traceability_evidence_packet/setup_source_sink_values.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/residual_owner_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_s12_thermal_source_property_freeze_gate/heat_path_residual_owner_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate/passive_heat_path_source_basis_table.csv
tags: [heat-loss, power-partition, calibration-design, residual-owner]
related:
  - .agent/status/2026-07-22_TODO-1D-FINAL-HEAT-LOSS-POWER-PARTITION-CALIBRATION-DESIGN-2026-07-22.md
  - .agent/journal/2026-07-22/1d-final-heat-loss-power-partition-calibration-design.md
  - imports/2026-07-22_1d_final_heat_loss_power_partition_calibration_design.json
task: TODO-1D-FINAL-HEAT-LOSS-POWER-PARTITION-CALIBRATION-DESIGN-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Writer / Reviewer / Tester
type: work_product
status: complete
---
# 1D Heat-Loss / Power-Partition Calibration Design

Decision: `heat_loss_power_partition_design_ready_no_calibration_no_release`.

This package designs the segmentwise heat-loss and power-partition calibration
study that must happen before any internal `Nu` tuning. It does not calibrate,
fit, release, freeze, or score a model.

## Current Evidence

The setup source/sink evidence is traceable but not released as a final runtime
source/property package:

- heater setup total across Salt1-Salt4 rows: `1133.1 W`;
- cooler/HX setup total: `-449.96244353013935 W`;
- test-section setup total: `148.0 W`.

PASSIVE-H2 provides diagnostic sensitivity only:

- nominal diagnostic passive operator: `873.2718786177952 W`;
- convective component: `216.7791447688486 W`;
- radiative component: `656.4927338489465 W`;
- largest passive sensitivity delta: `656.4927338489466 W`;
- numeric passive heat-loss release: `false`.

These values show why heat-loss ownership matters, but they do not license a
global UA multiplier, realized `wallHeatFlux` runtime input, imposed cooler duty
runtime input, or validation-temperature tuning.

## Calibration Design Principle

Calibrate or bound heat paths in this order:

1. independent setup source/sink provenance;
2. material/geometry resistance network;
3. setup-only external convection and radiation;
4. train/support-only uncertainty smoke;
5. residual-owner diagnosis;
6. candidate freeze only after source/property and same-QOI UQ gates pass.

Internal `Nu` is never the place to hide missing heater, cooler, passive,
radiation, storage, wall conduction, jacket, test-section, recirculation, or
unknown residual heat.

## Outputs

- `measurement_input_matrix.csv`
- `calibration_sequence.csv`
- `no_double_counting_checks.csv`
- `split_role_and_runtime_policy.csv`
- `figure_table_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
