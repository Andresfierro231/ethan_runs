---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_c_implementation/README.md
tags: [journal, fluid, external-boundary, runtime-contract]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21.md
  - imports/2026-07-21_fluid_external_bc_phase_c_implementation.json
task: TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21
date: 2026-07-21
role: Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Fluid External BC Phase C Implementation

## Attempted

Implemented a file-facing parser for the repo-local external-boundary runtime
dictionary and connected it to Fluid scenario loading through an optional
`external_boundary_dictionary_path`.
Added solver-side external-boundary contract validation so predictive runtime
rows are checked for known parents, supported selectors, finite setup fields,
predictive-only modes, source/sink exclusion, and forbidden runtime shortcut
fields before `solve_case` proceeds.

## Observed

The Fluid tree already had dirty external-boundary solver and solver-test
changes. Those existing paths include runtime validation and external-boundary
accounting. This row preserved that current structure and added a narrow
pre-solve validator rather than changing campaign/config defaults.

Focused Phase C pytest passed. The broad existing `test_solver_contracts.py`
suite was interrupted after 34 passing tests and no failures because it exceeded
the interactive validation window.

## Inferred

The next meaningful progress is not another parser change. It is a constrained
Phase D smoke-scorecard row that exercises one small train/support path and
audits the heat-path ledger/source labels for runtime leakage.

## Caveats

No Fluid campaign was launched and no model score/admission claim was made.
Explicit segment-map review is still required before production scenario
configuration.
