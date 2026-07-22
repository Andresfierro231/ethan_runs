---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/README.md
  - .agent/BOARD.md
tags: [thesis-dossier, study-execution, workflow]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/per_study_execution_packets.md
task: TODO-THESIS-STUDY-EXECUTION-DOCUMENTATION-PACKAGE-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Study Execution Workflow

## Phase 0 - Claim And Read

1. Claim exactly one board row.
2. Read that row, this package, the thesis next-studies dispatch, `.agent/BLOCKERS.md`, and every package named in the row's read-only context.
3. Confirm no active agent owns the files to be edited.
4. Open a task package under the board row's allowed `work_products/**` path.

## Phase 1 - Pre-Registration

Before computing or writing results, create a package README section or
`pre_registration.md` containing:

- study question and null/negative outcome;
- candidate inputs and forbidden inputs;
- row universe and split roles;
- metrics and pass/fail gates;
- source files and expected output files;
- exact reason the study can feed or cannot feed S11/S6.

No model choice may be revised after looking at holdout, external-test, or
future rows.

## Phase 2 - Evidence Assembly

Collect evidence into tables before interpretation:

- source manifest with exact paths;
- row inventory with split role and source-validity label;
- runtime-input audit;
- metric table or blocked metric placeholder;
- acceptance gate matrix;
- figure/table manifest.

Every table must distinguish observed CFD evidence, diagnostic reductions,
admitted runtime inputs, score-only targets, and blocked future rows.

## Phase 3 - Analysis

Run only the analysis permitted by the row:

- documentation-only rows may not launch samplers, solvers, or scheduler jobs;
- source/harvest rows may not admit closures unless the row explicitly says so;
- candidate rows may evaluate train/support evidence but may not tune against
  holdout, external, or future rows;
- trigger-gated rows must stop when the trigger is absent.

## Phase 4 - Interpretation

Write the result in one of three states:

- `admission_ready`;
- `negative_result`;
- `blocked_with_exact_next_action`.

Use `claim_admission_rules.md` to choose claim wording. If a result is blocked,
name the exact missing evidence and whether it requires a new board row.

## Phase 5 - Closeout

Close every study with:

- README and summary JSON;
- acceptance gate matrix;
- runtime leakage audit;
- source manifest;
- status file;
- journal entry;
- import manifest;
- `finish_task.py` validation.

If the study produces a thesis-ready figure or table, add a figure/table
manifest row with destination chapter and claim boundary.
