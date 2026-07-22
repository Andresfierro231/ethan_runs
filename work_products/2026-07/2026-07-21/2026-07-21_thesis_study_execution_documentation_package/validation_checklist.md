---
provenance:
  - tools/docs/build_repo_index.py
  - tools/agent/finish_task.py
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/required_artifacts_and_schemas.csv
tags: [thesis-dossier, validation, closeout]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/README.md
task: TODO-THESIS-STUDY-EXECUTION-DOCUMENTATION-PACKAGE-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Validation Checklist

## Required Commands

- `python3.11 tools/docs/build_repo_index.py --check`
- `python3.11 tools/agent/finish_task.py --task-id <TASK>`
- `python3.11 -m json.tool <package>/summary.json`
- `python3.11 -m json.tool imports/<date>_<slug>.json`

## Required File Checks

- README frontmatter has `provenance`, `tags`, `related`, `task`, `date`,
  `role`, `type`, and `status`.
- Every CSV has a header and at least one data row unless it is explicitly a
  template file.
- Every source path cited in a decision table exists or is labeled
  `external/unavailable` with a reason.
- The runtime leakage audit has explicit rows for all forbidden inputs.
- The acceptance gate matrix has no ambiguous final gate state.

## Review Checks

- Negative results identify failed gates rather than using vague language.
- Candidate studies do not use holdout, external, or future rows for selection.
- Upcomer ordinary `Nu/f_D/K`, F6, component K, and final predictive accuracy
  are not claimed unless their admission gates pass.
- Figures and tables have destination chapters and claim boundaries.
