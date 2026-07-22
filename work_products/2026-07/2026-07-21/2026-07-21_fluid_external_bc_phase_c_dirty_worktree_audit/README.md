---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_b_exact_file_preflight/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_b_exact_file_preflight/external_file_manifest.csv
tags: [fluid-external-boundary, dirty-worktree, implementation-preflight]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-C-DIRTY-WORKTREE-AUDIT-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-external-bc-phase-c-dirty-worktree-audit.md
task: TODO-FLUID-EXTERNAL-BC-PHASE-C-DIRTY-WORKTREE-AUDIT-2026-07-21
date: 2026-07-21
role: Coordinator/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---

# Fluid External BC Phase C Dirty-Worktree Audit

This package implements the repo-local pre-implementation audit for external Fluid Phase C. It did not edit external `../cfd-modeling-tools/**`.

## Finding

Phase C is feasible but should not start as a blind patch. The external Fluid worktree is already dirty in the Phase C-relevant files, and those dirty changes already include partial external-boundary-table support in `config_loader.py`, `solver.py`, and `tests/test_solver_contracts.py`. Phase C must build on the current dirty state, preserve unrelated AMX/UMX/TSWFC/config work, and avoid claiming dirty scenario/campaign configs by default.

## Files

- `dirty_file_diff_inventory.csv`: current dirty files and Phase C action.
- `ownership_conflict_table.csv`: conflict/ownership risks and required handling.
- `phase_c_exact_claim_recommendation.csv`: exact implementation claim recommendation.
- `test_file_necessity.csv`: test edit/add decision.
- `phase_c_board_update_text.md`: exact row update text for Phase C.
- `scheduler_snapshot.csv`: read-only current scheduler state for related monitor jobs.
- `source_manifest.csv`: inspected sources and commands.
- `summary.json`: machine-readable audit result.

## Go / No-Go

Go for Phase C only after the Phase C board row is updated with exact external paths and explicit external write approval. The first implementation should add `external_boundary.py` and `tests/test_external_boundary_contract.py`, then minimally integrate with the existing dirty `config_loader.py` and `solver.py`. Avoid dirty config files and existing broad solver-contract tests unless the implementation truly changes existing defaults.
