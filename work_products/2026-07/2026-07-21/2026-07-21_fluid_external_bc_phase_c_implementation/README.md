---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_b_exact_file_preflight/parser_api_contract.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_b_exact_file_preflight/unit_test_matrix.csv
tags: [fluid, external-boundary, runtime-contract, no-admission]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-external-bc-phase-c-implementation.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_c_dirty_worktree_audit/README.md
task: TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21
date: 2026-07-21
role: Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Fluid External BC Phase C Implementation

## Outcome

Phase C implemented the file-facing Fluid external-boundary dictionary path and
validated it against the Phase B contract. The new parser reads the repo-local
CSV/JSON runtime dictionary, filters by `case_id`, requires an explicit
`external_boundary_segment_map`, converts only predictive passive rows into
`external_boundary_role_rows`, and rejects forbidden realized-output shortcuts.
The solver now also validates external-boundary role rows before solving, so
unknown parent targets, unsupported selectors, non-predictive runtime rows,
source/sink roles, validation-temperature fields, and forbidden runtime shortcut
columns fail before model execution.

## Changed Artifacts

- `changed_external_files.csv`
- `runtime_leakage_audit.csv`
- `validation_commands.csv`
- `source_manifest.csv`
- `summary.json`

## Validation

All validation was local unit/compile/import validation. The focused Phase C
pytest passed. The broad existing solver contract suite was interrupted after
34 passing tests and no failures because it was too long for interactive
closeout. No Fluid campaign, CFD postprocessing, scheduler job, fitting,
scoring, or admission was launched.

## Remaining Work

The next row should be Phase D smoke-scorecard execution. It should run only a
small train/support Fluid path, audit heat-path ledger/source labels, and check
that no realized `wallHeatFlux`, CFD `mdot`, validation temperatures, imposed
cooler duty, or residual fill enters predictive runtime.
