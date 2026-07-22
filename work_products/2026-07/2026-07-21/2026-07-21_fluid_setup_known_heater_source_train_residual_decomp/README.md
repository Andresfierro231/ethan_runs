---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/train_solve_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/phase_f_thermal_residual_decomposition/sensor_segment_residuals.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/setup_known_source_contract.csv
tags: [fluid, setup-known-source, heater-source, train-only, residual-decomposition]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract
task: TODO-FLUID-SETUP-KNOWN-HEATER-SOURCE-TRAIN-RESIDUAL-DECOMP-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
---
# Setup-Known Heater Source Train Residual Decomposition

This package runs one bounded local Fluid `solve_case` for Salt2 train/support
using the existing `heater_source_mode=tw4_to_tp3_three_span` source lane.

Decision: `source_lane_partial_improvement_model_form_still_needed`.

- worker status: `pass`
- root status: `accepted`
- validation/holdout/external rows consumed: `0/0/0`
- freeze/admission/fitting: `false`

The output is train-only diagnostic evidence. It does not release S11, S15, S6,
or final predictive scores.
