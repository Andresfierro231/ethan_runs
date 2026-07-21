---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_c_dirty_worktree_audit/README.md
tags: [fluid-external-boundary, dirty-worktree, implementation-preflight]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-C-DIRTY-WORKTREE-AUDIT-2026-07-21.md
  - imports/2026-07-21_fluid_external_bc_phase_c_dirty_worktree_audit.json
task: TODO-FLUID-EXTERNAL-BC-PHASE-C-DIRTY-WORKTREE-AUDIT-2026-07-21
date: 2026-07-21
role: Coordinator/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---

# Fluid External BC Phase C Dirty-Worktree Audit

## Attempted

Inspected the external Fluid worktree read-only before Phase C implementation. Focused on the exact files named by the Phase B preflight and the dirty config/test files that could conflict with implementation.

## Observed

The external worktree is dirty in several Phase C-relevant files. `config_loader.py`, `solver.py`, and `test_solver_contracts.py` already include partial external-boundary-table support. `configs/scenarios.yaml` and `configs/campaigns.yaml` have large unrelated diagnostic additions and should not be claimed for the first parser/API implementation.

Scheduler read-only snapshot showed `3299610`, `3299620`, and `3307441` running; no harvest/admission row is justified from this audit.

## Inferred

Phase C can proceed, but the lowest-conflict implementation route is to add a new `external_boundary.py` parser module and a new focused `test_external_boundary_contract.py`, then minimally integrate with the current dirty `config_loader.py` and `solver.py`. Existing `test_solver_contracts.py` should be conditional rather than a default broad edit.

## Caveats

No external Fluid tests were run because this row is read-only and does not edit external code. The audit did not judge scientific correctness of the dirty external changes; it only records ownership and conflict boundaries.

## Next Useful Actions

Update `TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21` with the exact claim text in `phase_c_board_update_text.md` after external write approval. Then implement only the parser/API and runtime guardrail scope.
