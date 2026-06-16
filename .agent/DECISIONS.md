# Decisions

## 2026-06-09

- Repo-level coordination lives in `.agent/` so agents launched from
  subdirectories can share the same board, ownership map, journal policy, and
  cleanup rules.
- Root `AGENTS.md` is the first instruction file every agent must read.
- `JOURNAL.md` is the curated journal. Raw append-only agent notes go under
  `.agent/journal/YYYY-MM-DD/`.
- Shared process files such as `.agent/BOARD.md` and
  `.agent/FILE_OWNERSHIP.md` require coordinator approval.
- No agent may claim broad destructive cleanup authority over `staging/`,
  `linked_cases/`, `work_products/`, `reports/`, `tmp_extract/`, or
  `jadyn_runs/` without a dry-run inventory and explicit confirmation.
- Login-node safety is mandatory. Long rendering, full-case extraction, and
  solver runtime work must be deferred to appropriate batch or compute-node
  workflows.
- High-coordination subtrees may carry short `AGENTS.override.md` files. The
  helper script should surface those automatically from the current working
  directory toward repo root.
- The Salt 2 hydraulic analysis framework is split into a major-loss layer and
  a feature-based minor-loss layer. Major-loss reporting is legwise and
  centerline-based. Minor-loss reporting is pressure-budget-first.
- The first hydraulic implementation target is
  `val_salt_test_2_coarse_mesh_laminar` only, using the late retained wall-field
  window rather than a full transient history.
- The test-section side branch is treated as its own major leg, while tee
  entry/exit and connector effects remain in the minor-loss feature budget.

## 2026-06-10

- The next Salt 2 analysis pass is promoted from a Salt 2 only hydraulic
  package into a reusable per-case framework with one shared manifest and case
  profile contract.
- The shared manifest freezes requested retained times, target `ds`, required
  fields, and sign conventions before downstream extractors run.
- The initial common profile layer supports `val_salt_test_2_coarse_mesh_laminar`
  only, but the builder and extractor interfaces now depend on a profile lookup
  rather than direct Salt 2 constants.
- The June 10 package target is
  `reports/2026-06-10_ethan_salt2_case_analysis_package/`.
- The legacy June 9 hydraulic builder remains callable as a thin wrapper around
  the shared case-analysis package builder.
