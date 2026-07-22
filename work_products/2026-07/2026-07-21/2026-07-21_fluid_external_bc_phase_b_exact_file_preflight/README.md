---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_handoff_stubs.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/runtime_leakage_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [fluid, external-boundary, runtime-contract, preflight]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-B-EXACT-FILE-PREFLIGHT-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-external-bc-phase-b-exact-file-preflight.md
  - imports/2026-07-21_fluid_external_bc_phase_b_exact_file_preflight.json
task: TODO-FLUID-EXTERNAL-BC-PHASE-B-EXACT-FILE-PREFLIGHT-2026-07-21
date: 2026-07-21
role: Coordinator/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Fluid External BC Phase B Exact-File Preflight

## Decision

Phase B inspected the external Fluid repo read-only and names exact files for the
next implementation row. The implementation should be a narrow parser/API
hardening pass around the existing `outer_closure_mode: external_boundary_table`
path, not a broad solver rewrite.

## Exact External Files For Phase C

Claim these external paths before editing:

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/external_boundary.py` - new parser/API module for CSV dictionary import, normalization, runtime leakage rejection, and conversion to Fluid role rows.
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py` - integrate optional scenario fields that load the external-boundary dictionary into `ScenarioConfig.external_boundary_role_rows`.
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py` - add runtime validation for external boundary role rows and extend role-row heat accounting so predictive convection/radiation/layer semantics are explicit and auditable.
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md` - document the file-facing external-boundary contract and forbidden runtime inputs.
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_external_boundary_contract.py` - new unit tests for parser/API, leakage rejection, segment mapping, and role-row heat lanes.
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py` - only if `ScenarioConfig` defaults or existing external-boundary tests need updates.

Do not claim `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/scenarios.yaml`
unless Phase C intentionally adds a smoke scenario. The safer first pass is a
unit-tested parser/API with no default campaign mutation.

## Current External State

The external Fluid worktree is already dirty in several likely Phase C files:
`config_loader.py`, `solver.py`, `README.md`, `tests/test_solver_contracts.py`,
and config files. Phase C must inspect those diffs and coordinate before
editing. This Phase B task made no external changes.

## Outputs

- `exact_file_implementation_plan.md`
- `parser_api_contract.md`
- `unit_test_matrix.csv`
- `external_file_manifest.csv`
- `segment_mapping_contract.csv`
- `migration_no_mutation_notes.md`
- `phase_c_row_update_instructions.md`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Runtime design must reject realized CFD `wallHeatFlux`, CFD `mdot` shortcuts,
validation temperatures, hidden residual fills, imposed cooler duty, and
double-counted radiation. Replay total heat and predictive convection/radiation
must stay mutually exclusive.
