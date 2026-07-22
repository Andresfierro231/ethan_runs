---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract/recirculation_switch_lane_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_litrev_final_uc01_uc08_thesis_gap_crosswalk/uc01_uc08_thesis_gap_crosswalk.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory/summary.json
tags: [reverse-flow, recirculation, switching, calibration-design, no-coefficients]
related:
  - .agent/status/2026-07-22_TODO-1D-FINAL-REVERSE-FLOW-SWITCHING-CALIBRATION-DESIGN-2026-07-22.md
  - .agent/journal/2026-07-22/1d-final-reverse-flow-switching-calibration-design.md
  - imports/2026-07-22_1d_final_reverse_flow_switching_calibration_design.json
task: TODO-1D-FINAL-REVERSE-FLOW-SWITCHING-CALIBRATION-DESIGN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Forward-pred / Writer / Reviewer / Tester
type: work_product
status: complete
---
# 1D Reverse-Flow Switching Calibration Design

Decision: `reverse_flow_switching_design_complete_no_calibration_no_admission`.

This package executes the UC-03 design step. It defines how a future 1D model
should distinguish local wall-region reversal, core-wall counterflow, localized
recirculation, negative net branch flow, and zero-net-flux exchange before
activating MF-03/MF-04 style switching.

No switching coefficient is fitted or admitted. Current output is a runnable
design and missing-input ledger.

## Result

The current safe switch remains the dry three-lane contract:

- one-stream ordinary closure: disabled for current recirculating upcomer rows;
- signed-flow junction network: diagnostic fallback;
- throughflow plus recirculation exchange cell: architecture only, not admitted.

## Outputs

- `switching_state_taxonomy.csv`
- `calibration_metric_contract.csv`
- `missing_input_ledger.csv`
- `activation_gate.csv`
- `future_execution_plan.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No scheduler launch, native-output mutation, source/property release, Qwall
release, coefficient admission, protected scoring, or residual absorption into
internal Nu/fD/K/F6 occurred.
