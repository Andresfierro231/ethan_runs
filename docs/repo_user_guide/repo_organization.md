---
provenance:
  - AGENTS.md
  - README.md
  - .agent/FILE_OWNERSHIP.md
tags: [repo-user-guide, organization, provenance]
related:
  - docs/repo_user_guide/data_and_provenance.md
  - docs/repo_user_guide/common_tasks.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# Repo Organization

`ethan_runs/` is organized around scientific evidence flow:

1. source case is made reachable;
2. case is staged or registered;
3. provenance is recorded;
4. extraction/analysis creates task-scoped artifacts;
5. status/journal/import docs preserve the result;
6. publication-ready summaries can move to the canonical comparison repo.

## Coordination Layer

| Path | Meaning |
| --- | --- |
| `.agent/BOARD.md` | Live task queue and allowed edit paths. |
| `.agent/FILE_OWNERSHIP.md` | Shared path ownership and conflict rules. |
| `.agent/ROLES.md` | Role definitions for Coordinator, Implementer, Tester, Reviewer, Writer, Cleaner. |
| `.agent/status/` | Task outcome summaries. |
| `.agent/journal/` | Dated raw observations and reasoning. |
| `.agent/blockers.yml` | Curated blocker register. |
| `.agent/STATE.md`, `.agent/BLOCKERS.md`, `.agent/catalog.*` | Generated current state and searchable catalog. |

## Data and Evidence Layer

| Path | Meaning |
| --- | --- |
| `imports/` | Dated manifests for changed files, read-only context, and mutation flags. |
| `registry/` | Case registry. Mutate only under assigned scope. |
| `work_products/` | Reproducible generated packages and tables. |
| `reports/` | Report, thesis, and presentation packages. |
| `operational_notes/` | Dated handoffs and living topic maps. |
| `reference/` | Shared factual references, especially geometry and naming truth. |

## Source and Staging Layer

| Path | Meaning |
| --- | --- |
| `jadyn_runs/` | Campaign workspaces, launch scripts, and staged run families. |
| `staging/` | Local staged copies, render inputs, and generated staging products. |
| `linked_cases/` | Symlink convenience handles only; do not cite as provenance. |
| `tmp/`, `tmp_extract/`, `cache/` | Scratch/generated material. Inspect before cleanup. |

## Tool Layer

| Path | Meaning |
| --- | --- |
| `tools/agent/` | Board, closeout, lint, and background-compute helpers. |
| `tools/analyze/` | Package builders, scorecard builders, and analysis tests. |
| `tools/extract/` | CFD extraction, sampling, VTK/OpenFOAM helpers, rendering. |
| `tools/intake/` | Case registration and import manifests. |
| `tools/publish/` | Cross-model publication, backup, transfer, download helpers. |
| `tools/docs/` | Generated docs index and tool inventory builders. |

## Local Instructions

Before touching a subtree, read the nearest local instruction:

- `tools/AGENTS.override.md` for tooling edits;
- `reports/AGENTS.override.md` for report/thesis work;
- `staging/AGENTS.override.md` before staged-copy or rendering work;
- `jadyn_runs/AGENTS.override.md` before campaign work.

## Generated Versus Native

Native solver outputs live in case trees and are protected. Generated artifacts
live under task-scoped paths such as `work_products/<date>/<package>/`,
`reports/<date>/<package>/`, `figures*`, and staging/render outputs. Generated
does not mean disposable: inspect provenance and ownership first.
