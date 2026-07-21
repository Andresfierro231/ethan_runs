---
provenance:
  - tools/analyze/build_fluid_external_bc_dict.py
  - tools/analyze/test_fluid_external_bc_dict.py
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/summary.json
tags: [thermal-modeling, external-boundary, fluid, status]
related:
  - .agent/journal/2026-07-21/fluid-external-bc-dict.md
  - imports/2026-07-21_fluid_external_bc_dict.json
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
task: TODO-FLUID-EXTERNAL-BC-DICT
date: 2026-07-21
role: Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-FLUID-EXTERNAL-BC-DICT

## Objective

Implement the repo-local external-boundary dictionary contract/validator
package needed before a future external Fluid source row can add first-class
runtime support for external convection, radiation, and layer resistance.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/`.

- Runtime dictionary rows: `24`.
- Predictive passive external rows: `15`.
- Document-only source/sink rows: `9`.
- Runtime schema rows: `18`.
- Allowed runtime modes: `4`.
- Validation cases: `5`.
- Fluid handoff stubs: `3`.

The package separates predictive external convection/radiation/layer inputs
from replay/diagnostic total heat. It excludes realized heat flux, CFD `mdot`,
imposed cooler duty, validation temperatures, and residual-derived field fills
from predictive runtime inputs.

## Changes Made

- `tools/analyze/build_fluid_external_bc_dict.py`
- `tools/analyze/test_fluid_external_bc_dict.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_schema.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/allowed_runtime_mode_table.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/validation_cases.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_handoff_stubs.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/runtime_leakage_audit.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/external_bc_runtime_field_contract.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/external_bc_representative_dictionary_rows.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/external_bc_mode_policy.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/external_bc_validation_cases.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_api_handoff_stubs.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/summary.json`
- `.agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-DICT.md`
- `.agent/journal/2026-07-21/fluid-external-bc-dict.md`
- `imports/2026-07-21_fluid_external_bc_dict.json`
- `.agent/BOARD.md` own row update

## Validation

- `python3.11 -m unittest tools.analyze.test_fluid_external_bc_dict`:
  passed, `6` tests.
- `python3.11 -m py_compile tools/analyze/build_fluid_external_bc_dict.py tools/analyze/test_fluid_external_bc_dict.py`:
  passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict`:
  passed.

## Unresolved Blockers

- External Fluid API/source integration still needs a separate row claiming
  exact files under the external Fluid repository.
- Phase 2 of the forward plan still needs upcomer exchange-state extraction:
  `V_recirc`, `mdot_exchange`, `tau_recirc`, wall-core Delta T, pressure
  residual, energy residual, and same-QOI UQ.

## Guardrails

- External Fluid source: not edited.
- Native solver outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: not touched.
- Solver/postprocessing: not launched.
- Fitting/tuning/model selection: not performed.
- Closure admission: not changed.
- Blocker register: not edited.
- Generated docs index: not refreshed because this row did not claim it.
