# AGENTS.md

Reviewed: `2026-06-09T00:00:00-05:00`

## Workspace role

`ethan_runs/` is the heavy-data intake and preprocessing workspace for
Ethan-provided CFD cases that later publish durable summaries into
`../cfd-modeling-tools/cross_model_comparison`.

This repo is not a generic software project. It combines:

- intake and registration state in `imports/`, `registry/`, and `config/`
- analysis and publication scripts in `tools/`
- staged case trees in `staging/` and campaign workspaces in `jadyn_runs/`
- generated figures and extracted artifacts in `figures*`, `work_products/`,
  `tmp_extract/`, and `reports/`
- research context in `journals/`, `operational_notes/`, and report markdown

## Required startup protocol

Any agent launched from the repo root or any subfolder must do this first:

1. Locate the repo root.
2. Read this root `AGENTS.md`.
3. Read `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`, and `.agent/ROLES.md`.
4. Read relevant local instructions for the subtree being touched.
   Read any nearest `AGENTS.override.md` first, then the nearest `README.md`,
   `TODO.md`, campaign dossier, or report package README in `jadyn_runs/`,
   `reports/`, `operational_notes/`, `staging/`, or `tools/`.
5. Identify a role before editing:
   `Coordinator`, `Implementer`, `Tester`, `Reviewer`, `Writer`, or `Cleaner`.
6. Confirm a task ID and allowed edit paths on `.agent/BOARD.md`.
7. Refuse unassigned work or edits that overlap another active agent's files.

Use `.agent/scripts/agent_context.sh` when starting from a subdirectory.

## Non-negotiable rules

- Never mutate native solver outputs in imported source directories.
- Treat `linked_cases/` symlinks as local convenience only, not provenance.
- Record exact source paths in manifests and published artifacts.
- Require local staging before analysis when a source originates on another
  machine or unavailable mount.
- Do not work on unassigned tasks.
- Do not edit files owned by another active agent.
- Keep changes small and reviewable.
- Update a status file, raw journal entry, or handoff at the end of work.
- Never run long or expensive jobs on login nodes.
- Ask before destructive cleanup, deletion, force-overwrite, or irreversible
  actions.

## Repo-specific operating rules

- Major intake or interpretive passes must write or update:
  - an import manifest in `imports/`
  - a case registry entry in `registry/case_registry.csv` when scope changes
  - a dated journal entry
  - a checkpoint or TODO when unresolved work remains
- `cross_model_comparison/` remains the canonical publication home for
  cross-model comparison campaigns, journals, and provenance indices.
- Prefer coordination files, helper scripts, and dated markdown over ad hoc
  scratch notes.
- Prefer reproducible scripts over manual artifact edits for `reports/`,
  `figures/`, `figures_rendered/`, and `work_products/`.
- Treat `staging/`, `tmp_extract/`, `cache/`, and generated figure trees as
  potentially large and sensitive. Inspect first. Do not broad-delete.

## Writing rules

- Use dated filenames when practical.
- Separate observed output, inferred interpretation, contradictions, and next
  suggested actions.
- Preserve abandoned or incomplete lines of investigation instead of silently
  dropping them.
- Cite source files, scripts, journals, reports, or figures for claims.
- Keep machine-local artifacts reproducible from scripts wherever possible.
