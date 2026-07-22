# Proposed Phase C Row Update

Replace the Phase C scope text with the following exact-path claim after
coordinator approval:

```text
TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21 | Implementer / Tester | open / external write approval required | .agent/BOARD.md (own row only), .agent/status/<date>_TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21.md, .agent/journal/<date>/fluid-external-bc-phase-c-implementation.md, imports/<date>_fluid_external_bc_phase_c_implementation.json, work_products/<date>_fluid_external_bc_phase_c_implementation/**, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/external_boundary.py, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md, external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_external_boundary_contract.py, conditional external ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py only if ScenarioConfig defaults or existing external-boundary tests change. READ-ONLY: repo-local Fluid external BC dictionary package, Phase B preflight package, external Fluid configs unless separately claimed, native CFD/OpenFOAM outputs, registry/admission state, scheduler state, thesis current files, generated docs index files, blocker register, and all other paths. No native-output mutation, registry/admission mutation, scheduler action, solver/postprocessing launch, fitting/tuning/model selection, closure admission, blocker-register change, generated-index refresh, or default campaign/config mutation unless explicitly added to scope.
```

Replace the Phase C goal text with:

```text
Implement the file-facing Fluid external-boundary parser/API and runtime guardrails named by Phase B. Use a new external_boundary.py parser module, integrate optional dictionary loading in config_loader.py, harden solver.py role-row validation/accounting, document README semantics, and add focused parser/runtime tests. Runtime must reject forbidden realized wallHeatFlux, CFD mdot shortcuts, validation temperatures, hidden residual fills, imposed cooler duty, and double-counted radiation. No Fluid campaign/config mutation or smoke scorecard in this row unless the row is explicitly expanded after coordination.
```

Coordination note: the external Fluid worktree is already dirty in several
likely Phase C files. The implementation agent must inspect current diffs before
patching and must not overwrite other agents' work.
