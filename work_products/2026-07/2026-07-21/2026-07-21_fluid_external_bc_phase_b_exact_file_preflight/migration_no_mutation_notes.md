# Migration And No-Mutation Notes

## External Repo

This phase inspected `../cfd-modeling-tools/**` read-only. No external files
were edited.

The external Fluid worktree is dirty before Phase C. Relevant dirty paths
reported by `git -C ../cfd-modeling-tools/tamu_first_order_model/Fluid status --short`:

- `configs/campaigns.yaml`
- `configs/scenarios.yaml`
- `tamu_loop_model_v2/README.md`
- `tamu_loop_model_v2/config_loader.py`
- `tamu_loop_model_v2/solver.py`
- `tests/test_solver_contracts.py`
- additional unrelated AMX/TSWFC files and journals

Phase C must inspect these existing changes and avoid overwriting them.

## Native Outputs And Registry

No native CFD/OpenFOAM outputs were read as mutable sources or edited. No
registry/admission state was mutated. No scheduler action, solver launch,
postprocessing launch, fitting, model selection, or closure admission was
performed.

## Migration Path

1. Add the parser in a new `external_boundary.py` module.
2. Add config-loader integration behind optional scenario fields.
3. Add solver validation and lane-level accounting for external role rows.
4. Add unit tests using synthetic CSV fixtures.
5. Only after tests pass, allow a later smoke row to claim a small execution
   path and produce a runtime leakage audit.

## Non-Admission Boundary

Passing Phase C tests must not be treated as a heat-loss model admission. It
only proves that the runtime contract is enforceable and the parser/API path is
usable.
