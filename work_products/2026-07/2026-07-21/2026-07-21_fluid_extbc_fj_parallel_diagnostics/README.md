---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/thermal_residual_attribution.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/segment_states.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/heat_path_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/role_row_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_b_exact_file_preflight/segment_mapping_contract.csv
tags: [forward-model, external-bc, train-only, residual-attribution]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-FJ-PARALLEL-DIAGNOSTICS-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-extbc-fj-parallel-diagnostics.md
  - imports/2026-07-21_fluid_extbc_fj_parallel_diagnostics.json
task: TODO-FLUID-EXTBC-FJ-PARALLEL-DIAGNOSTICS-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Fluid External-BC F-J Parallel Diagnostics

This package uses the completed Phase E Salt2 train-only Fluid solve as a
diagnostic baseline. It does not freeze or admit a predictive model.

## Start Here

Open `summary.json`, then the Phase F dominant-owner table, Phase G missing-row
audit, Phase I admissibility matrix, and Phase J repair decision. These files
answer the current question: why the Phase E external-BC runtime path is useful
for diagnosis but not yet credible as a final predictive temperature path.

Trusted inputs are the completed Phase E train-only solve, the repo-local
external-BC dictionary, and the Phase B mapping contract. All are read-only in
this package. The unresolved blockers are: Salt1 external-BC dictionary rows
are absent, source/sink rows remain document-only/forbidden, and non-baseline
heat-loss sensitivities require a separate compute-safe subprocess or scheduler
row because the first foreground perturbation exceeded practical runtime.

## Outputs

- `phase_f_thermal_residual_decomposition/`: segment and source-family thermal residual ownership.
- `phase_g_dictionary_completeness_audit/`: external-BC row completeness, Salt1 gaps, document-only rows, units, signs, and mapping coverage.
- `phase_h_heatloss_network_sensitivity/`: bounded local train-only Fluid sensitivities.
- `phase_i_source_sink_admissibility/`: strict runtime admissibility matrix for heater/cooler/test-section source/sink rows.
- `phase_j_train_repair_decision/`: one-change repair decision; fail-closed when no legal deterministic correction exists.

## Result

The Phase E runtime path is executable, but thermal residuals remain diagnostic.
Phase J did not run a repair solve because no non-fitting legal correction was
released by Phase G or Phase I.

## Output Contract

All claims are train/support diagnostics only. Validation, holdout, and
external-test rows are not runtime inputs and are not scored. Do not use Phase H
blocked rows as fitted evidence. Do not convert the Phase J no-run decision into
admission; it is a blocker record for the next compute-safe sensitivity row.
