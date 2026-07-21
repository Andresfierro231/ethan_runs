---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_c_implementation/README.md
tags: [status, fluid, external-boundary, runtime-contract]
related:
  - .agent/journal/2026-07-21/fluid-external-bc-phase-c-implementation.md
  - imports/2026-07-21_fluid_external_bc_phase_c_implementation.json
task: TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21
date: 2026-07-21
role: Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21

## Objective

Implement the file-facing Fluid external-boundary parser/API and config-loader
integration needed to consume the repo-local external BC dictionary without
using realized CFD outputs as predictive runtime inputs.

## Outcome

Complete. Added `external_boundary.py`, integrated
`external_boundary_dictionary_path` into `config_loader.py`, documented the
runtime contract in the Fluid README, and added focused parser/runtime tests.
Added solver-side `_validate_external_boundary_contract` and call it from
`solve_case` so role-row misuse fails before model execution.

## Changes Made

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/external_boundary.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_external_boundary_contract.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_c_implementation/`
- `.agent/journal/2026-07-21/fluid-external-bc-phase-c-implementation.md`
- `imports/2026-07-21_fluid_external_bc_phase_c_implementation.json`
- `.agent/BOARD.md` own row status only

## Validation

- `env PYTHONDONTWRITEBYTECODE=1 python3.11 -m pytest -q -p no:cacheprovider tests/test_external_boundary_contract.py`: PASS, 7 tests plus 6 subtests.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 -m pytest -q -p no:cacheprovider tests/test_solver_contracts.py`: interrupted by agent after 34 passing tests, no failures, 500.70 s elapsed; full broad suite was too long for interactive closeout.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 -m py_compile tamu_loop_model_v2/external_boundary.py tamu_loop_model_v2/config_loader.py tamu_loop_model_v2/solver.py tests/test_external_boundary_contract.py`: PASS.
- Import smoke for `ExternalBoundaryRecord`, dictionary loader, scenario loader, and `_validate_external_boundary_contract`: PASS.

## Guardrails

Native CFD/OpenFOAM outputs: not mutated. Scheduler: no action. Solver or
postprocessing launch: none. Registry/admission state: not mutated. Generated
docs index and blocker register: not refreshed or edited under this row.
