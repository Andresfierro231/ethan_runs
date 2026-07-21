---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/runtime_leakage_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [fluid, external-boundary, journal]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-B-EXACT-FILE-PREFLIGHT-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_b_exact_file_preflight/README.md
task: TODO-FLUID-EXTERNAL-BC-PHASE-B-EXACT-FILE-PREFLIGHT-2026-07-21
date: 2026-07-21
role: Coordinator/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Fluid External BC Phase B Exact-File Preflight

## Attempted

Read the assigned board row, ownership and role files, the repo-local external
BC dictionary package, the heat-loss Phase 1 radiation integration package, and
the external Fluid local instructions. Then inspected the external Fluid source
read-only for existing parser, solver, API, and test surfaces.

## Observed

The repo-local dictionary already records the runtime leakage guardrails:
predictive mode excludes realized `wallHeatFlux`, CFD `mdot`, validation
temperatures, imposed cooler duty, and heat residual fills. The heat-loss Phase
1 package fixes the radiation rule: replay total `wallHeatFlux` cannot also add
separate predictive convection/radiation.

The external Fluid model already supports `outer_closure_mode:
external_boundary_table`, parent-level external boundary mappings, and inline
`external_boundary_role_rows`. Existing tests cover inline role rows and parent
mapping behavior in `tests/test_solver_contracts.py`.

The missing boundary is file-facing: there is no dedicated parser/API for the
repo-local CSV dictionary, no explicit external-boundary row validator called
from `solve_case`, and no focused tests that reject forbidden runtime inputs by
dictionary policy.

## Inferred

Phase C should add a small parser/API module instead of expanding the solver
with CSV parsing. `config_loader.py` should turn optional scenario dictionary
fields into existing `ScenarioConfig.external_boundary_role_rows`. `solver.py`
should own runtime validation and predictive heat accounting.

## Caveats

The external Fluid worktree is already dirty in likely implementation files.
Phase C must inspect those diffs and coordinate. This phase did not edit the
external repo and did not update the Phase C row directly.

## Next Useful Actions

1. Coordinator updates Phase C with the exact paths from
   `phase_c_row_update_instructions.md`.
2. Phase C implementation agent claims those paths and inspects existing
   external diffs.
3. Add parser/API tests before or alongside implementation.
4. Defer smoke execution and any scoring to the later smoke-scorecard row.
