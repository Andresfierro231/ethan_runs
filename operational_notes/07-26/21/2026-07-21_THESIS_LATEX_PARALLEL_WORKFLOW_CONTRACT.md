---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/README.md
  - reports/thesis_dossier/README.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/README.md
tags: [start-here, thesis, latex, csem, parallel-workflow]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/latex_sync_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/papers_board_rows.md
task: TODO-THESIS-LATEX-PARALLEL-WORKFLOW-CONTRACT-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: operational-note
status: reference
supersedes: []
superseded_by:
---
# Start Here: Thesis LaTeX Parallel Workflow

## Why This Exists

The CSEM thesis now has two active layers:

- `ethan_runs/reports/thesis_dossier/Chapters_and_sections/current/` contains
  copy-ready thesis prose and evidence ledgers.
- `../papers/UTexas_Research/csem-Masters_dissertation/` contains the actual
  LaTeX dissertation.

Parallel work needs a contract so one agent can write LaTeX while other agents
produce figures, tables, and analysis artifacts without weakening the
split/admission rules.

## Files To Open First

1. `work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/README.md`
2. `work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/latex_sync_contract.csv`
3. `work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/artifact_handoff_schema.json`
4. `work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/papers_board_rows.md`
5. `../papers/UTexas_Research/csem-Masters_dissertation/README.md`
6. `../papers/UTexas_Research/csem-Masters_dissertation/AGENTS.md`
7. `../papers/.agent/BOARD.md`

## Trusted Packages

Use the current thesis dossier, the dated `ethan_runs/work_products/**`
packages, and the papers CSEM dissertation scaffold. Treat native OpenFOAM/CFD
outputs as read-only.

## Work Sequence

1. Promote one LaTeX row from `papers_board_rows.md` into
   `../papers/.agent/BOARD.md` with an owner and exact paths.
2. Let artifact producers continue in `ethan_runs` using the schema in
   `artifact_handoff_schema.json`.
3. LaTeX writer imports only evidence whose package README states split role,
   admission state, allowed use, forbidden use, runtime-leakage audit, and
   validation result.
4. Run `scripts/check_guardrails.sh` and `scripts/build_thesis.sh` from the
   CSEM dissertation directory after each LaTeX sync row.
5. Use `csem-latex-integration-review-build-2026-07-21` as the review row after
   a set of chapter rows lands.

## Guardrails

- Do not invent results.
- Do not promote diagnostic CFD evidence to admitted predictive closure.
- Do not use CFD `mdot`, realized `wallHeatFlux`, imposed cooler duty,
  validation temperatures, holdout rows, or external-test rows as hidden
  predictive runtime inputs.
- Do not claim SAM validation. The thesis contribution is a vetted
  CSEM/SAM-relevant closure/admission workflow and branchwise evidence map.
- Do not let two writers edit the same `.tex` file under separate active rows.

## Output Contract

An `ethan_runs` artifact package is thesis-ready only when it has the fields in
`artifact_handoff_schema.json`. A papers LaTeX row is complete only when it
records changed paths, validation output, residual blockers, and claim
boundaries in papers status/journal files.
