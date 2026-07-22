# Recommended Phase C Board Update

Use this only after explicit external write approval.

```text
TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21 | Implementer / Tester | open / external write approval required | .agent/BOARD.md (own row only), .agent/status/<date>_TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21.md, .agent/journal/<date>/fluid-external-bc-phase-c-implementation.md, imports/<date>_fluid_external_bc_phase_c_implementation.json, work_products/<date>_fluid_external_bc_phase_c_implementation/**, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/external_boundary.py, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_external_boundary_contract.py, conditional external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py only if ScenarioConfig defaults/imports require compatibility updates. READ-ONLY: repo-local Fluid external BC dictionary package, Phase B exact-file preflight package, dirty-worktree audit package, external Fluid configs unless separately claimed, external Fluid reporting/materials files unless separately claimed, native CFD/OpenFOAM outputs, registry/admission state, scheduler state, thesis current files, generated docs index files, blocker register, and all other paths. No native-output mutation, registry/admission mutation, scheduler action, solver/postprocessing launch, fitting/tuning/model selection, closure admission, blocker-register change, generated-index refresh, campaign/config mutation, smoke scorecard, or overwrite of unrelated external dirty changes.
```

Goal text:

```text
Implement the file-facing Fluid external-boundary parser/API and runtime guardrails named by Phase B and constrained by the dirty-worktree audit. Add `external_boundary.py`, integrate optional dictionary loading in `config_loader.py`, harden `solver.py` role-row validation/accounting while preserving current dirty external_boundary_table support, document README semantics, and add focused parser/runtime tests. Runtime must reject forbidden realized wallHeatFlux, CFD mdot shortcuts, validation temperatures, hidden residual fills, imposed cooler duty, and double-counted radiation. No Fluid campaign/config mutation or smoke scorecard in this row.
```
