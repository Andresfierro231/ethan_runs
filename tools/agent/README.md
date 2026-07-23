---
provenance:
  - AGENTS.md
  - .agent/README.md
  - operational_notes/START_HERE_FOR_AGENTS.md
  - tools/agent/
tags: [agent-operations, tooling, documentation, handoff]
related:
  - operational_notes/maps/agent-operations.md
  - operational_notes/START_HERE_FOR_AGENTS.md
task: AGENT-491
date: 2026-07-17
role: Coordinator/Implementer/Tester/Writer
type: operational_note
status: reference
---
# Agent Tooling Reference

`tools/agent/` contains lightweight coordination helpers for `ethan_runs`.
They are intentionally stdlib-only and read-only by default. They do not replace
the board, status files, journals, import manifests, topic maps, or scientific
review; they make the required workflow easier to check.

Run commands from the repo root unless noted otherwise.

## Tool Summary

| Tool | Use before/after | Purpose |
|---|---|---|
| `preflight_task.py` | before editing | Confirm board scope and active edit-path conflicts. |
| `finish_task.py` | before closeout | Enforce minimum status/journal/import/index handoff. |
| `source_property_gate.py` | before scorecard closeout | Audit fit/admission rows for source/property labels and gate blockers. |
| `new_task.py` | before starting a new row | Scaffold task artifacts in dry-run or explicit-write mode. |
| `claim_task.py` | before starting a new row | Compatibility alias for `new_task.py` used by older handoffs. |
| `board_summary.py` | routine coordinator scans | Print bounded live-board counts, active rows, and completed rows still in Active. |
| `board_slice.py` | when task/query is known | Print one exact row or a small filtered board slice without dumping long scope text. |
| `board_row.py` | when task/query is known | Compatibility alias for `board_slice.py` used by older handoffs. |
| `task_context.py` | after choosing a task | Show edit paths, read-only lanes, conflicts, instruction files, and closeout artifact presence. |
| `board_archive.py` | after board hygiene | Move `## Archived ...` sections from the live board into `.agent/BOARD_ARCHIVE.md`. |
| `board_dashboard.py` | anytime | Print compact active/live agent and open TODO view. |
| `live_blockers.py` | startup / blocker scan | Print compact open blocker rows from generated `.agent/BLOCKERS.md` without long notes. |
| `scope_conflict_audit.py` | before claiming/narrowing rows | Report broad open edit-path claims and active path overlaps. |
| `safe_rg.py` | before repo searches | Guard broad ripgrep calls and stop after bounded output. |
| `status_scope.py` | before status checks | Require path-scoped `git status --short -- <paths>`. |
| `guardrail_summary.py` | before noisy validators | Run guardrail/lint commands and print bounded PASS/FAIL/NOTE lines. |
| `preview_csv.py` | before CSV inspection | Show selected columns/rows instead of dumping full evidence tables. |
| `read_csv_brief.py` | before CSV inspection | Compatibility alias for `preview_csv.py` used by older handoffs. |
| `package_brief.py` | before package inspection | Summarize package files, CSV headers/counts, scalar JSON, and README headings. |
| `package_digest.py` | before package inspection | Compatibility alias for `package_brief.py` used by older handoffs. |
| `gate_snapshot.py` | before gate-package review | Print bounded package decision, pass/blocker, closed-guardrail, and action-row summaries. |
| `manifest_check.py` | before manifest validation | Quiet JSON validation without pretty-printing full manifests. |
| `closeout_stub.py` | before closeout docs | Dry-run or write status/journal/import skeletons for the current task. |
| `closeout_bundle.py` | before closeout docs | Compatibility alias for `closeout_stub.py` used by older handoffs. |
| `link_report.py` | after publishing reports | Add report links to standard discovery files in dry-run or explicit-write mode. |
| `background_compute_helper.py` | before launching work | Choose `sbatch`, `srun`, or `tmux+srun` and list handoff fields. |
| `split_policy_lint.py` | before predictive docs closeout | Catch stale current split language. |
| `runtime_input_lint.py` | before predictive model closeout | Catch possible forbidden runtime-input leakage. |
| `case_schema_lint.py` | before CFD row admission | Check CFD-to-1D schema-lane coverage. |

## `preflight_task.py`

```bash
python3.11 tools/agent/preflight_task.py --task-id AGENT-491
python3.11 tools/agent/preflight_task.py --task-id AGENT-491 --json
```

Checks:

- task exists on `.agent/BOARD.md`;
- board status, role, owner, and line number;
- editable code-span paths before `READ-ONLY:`;
- read-only code-span paths after `READ-ONLY:`;
- active/open row edit-path overlap.

Exit behavior:

- `0`: task exists and no active conflict was detected;
- `1`: conflict was detected;
- `2`: task is missing from the board.

Limitations:

- It is a text parser for the board table, not a permission system.
- It intentionally ignores completed legacy rows when detecting active
  conflicts.

## `finish_task.py`

```bash
python3.11 tools/agent/finish_task.py --task-id AGENT-491
python3.11 tools/agent/finish_task.py --task-id AGENT-491 --json
python3.11 tools/agent/finish_task.py --task-id AGENT-491 --rebuild-index
```

Checks:

- board row is `STATUS: COMPLETE` or `STATUS: BLOCKED`;
- status file exists and documents changes, validation, and guardrails;
- journal entry exists and names the task;
- import manifest exists;
- manifest has `changed_files`, `read_only_context`, and mutation flags;
- every manifest `changed_files` path exists;
- scorecard-like changed CSVs trigger a warning-mode source/property gate audit
  unless the manifest declares `no_scorecard_outputs: true`;
- `tools/docs/build_repo_index.py --check` passes.

Exit behavior:

- `0`: minimum handoff contract passes;
- `1`: documentation or index check failed.

Use `--rebuild-index` only when the board row owns generated index files or no
active row blocks regeneration.

## `source_property_gate.py`

```bash
python3.11 tools/agent/source_property_gate.py <package-or-csv> --warn
python3.11 tools/agent/source_property_gate.py <package-or-csv> --strict
python3.11 tools/agent/source_property_gate.py <package-or-csv> --json
python3.11 tools/agent/source_property_gate.py <package-or-csv> --warn --todo-out work_products/<date>/<package>/source_property_todo.csv
```

Audits scorecard-like CSVs for fit/admission candidate rows and requires:

- `property_mode`
- `property_sensitivity_label`
- `source_validity_envelope_status`
- `source_use_category`
- `provenance_author_title`

Failure modes are reported separately so follow-up work can diagnose the gap:
missing label columns, blank labels, missing or blocked gate status,
refresh-required label content, outside/mixed source envelope, diagnostic/no-fit
source use, and candidate rows whose fit/admission flag is positive while the
source/property gate blocks them.

Default use in `finish_task.py` is warning mode. Warnings are deliberately loud
(`SOURCE_PROPERTY_GATE_WARNING`) but do not fail closeout yet. Use `--strict`
for a hard failure in a package-specific validation step. Use
`no_scorecard_outputs: true` in a task import manifest only when the task did
not create scorecard/admission/fit/gate CSV outputs.

## `new_task.py`

Dry-run default:

```bash
python3.11 tools/agent/new_task.py \
  --task-id AGENT-999 \
  --title "example coordination task" \
  --scope "`.agent/BOARD.md` (own row only), `.agent/status/<date>_AGENT-999.md`" \
  --goal "Document an example task."
```

Explicit write:

```bash
python3.11 tools/agent/new_task.py ... --write
```

Optional board insertion:

```bash
python3.11 tools/agent/new_task.py ... --write --write-board-row
```

Default behavior is dry-run to avoid accidental board edits. Written artifacts
are stubs only; the agent must still fill real context.

## `board_dashboard.py`

```bash
python3.11 tools/agent/board_dashboard.py
python3.11 tools/agent/board_dashboard.py --limit 10
```

Prints:

- total parsed board rows;
- open row count;
- active/live agent rows;
- open TODO rows.

This is for scanning, not for scientific status decisions.

## `board_summary.py`

```bash
python3.11 tools/agent/board_summary.py --limit 30
python3.11 tools/agent/board_summary.py --include-archive --limit 30
python3.11 tools/agent/board_summary.py --task-filter LITREV --active-only --limit 10
python3.11 tools/agent/board_summary.py --owner-filter codex --status-filter running --limit 10
python3.11 tools/agent/board_summary.py --json
```

Use this instead of broad board reads when checking coordination state. It
prints row counts by section/status, active rows needing attention, and completed
rows still sitting in Active.

## Low-Token Task Startup

Use this sequence when the task ID or topic is known:

```bash
python3.11 tools/agent/board_slice.py --task-id TODO-EXAMPLE-2026-07-22
python3.11 tools/agent/task_context.py --task-id TODO-EXAMPLE-2026-07-22
python3.11 tools/agent/live_blockers.py --limit 12
python3.11 tools/docs/state_brief.py --active --blockers
```

`board_slice.py` also supports bounded topic queries:

```bash
python3.11 tools/agent/board_slice.py --active --open --query S13 --limit 8
python3.11 tools/agent/board_slice.py --task-id TODO-EXAMPLE-2026-07-22 --full
python3.11 tools/agent/board_slice.py --query heat-loss --include-archive --json
```

Older handoffs may name equivalent aliases. These are supported and should be
treated as the same tools: `board_row.py` -> `board_slice.py`,
`claim_task.py` -> `new_task.py`, `package_digest.py` -> `package_brief.py`,
`read_csv_brief.py` -> `preview_csv.py`, and `closeout_bundle.py` ->
`closeout_stub.py`.

`task_context.py` is the preferred one-task permission/context view. It prints
only the selected row's editable paths, read-only context, active overlaps,
instruction files to read, and whether closeout artifacts already exist.

Use `scope_conflict_audit.py` when a row appears blocked by a broad optional
scope such as `tools/analyze/`:

```bash
python3.11 tools/agent/scope_conflict_audit.py --limit 20
python3.11 tools/agent/scope_conflict_audit.py --task-id TODO-EXAMPLE-2026-07-22
```

## Low-Output Inspection Tools

Use these before any command that could print hundreds or thousands of lines.

```bash
python3.11 tools/agent/safe_rg.py "pattern" chapters data --glob "*.tex" --max-lines 120
python3.11 tools/agent/safe_rg.py "pattern" . --glob "*.md" --max-count 5 --max-lines 80
python3.11 tools/agent/live_blockers.py --limit 12
python3.11 tools/agent/scope_conflict_audit.py --limit 20
python3.11 tools/agent/status_scope.py tools/agent operational_notes/START_HERE_FOR_AGENTS.md
python3.11 tools/agent/guardrail_summary.py -- scripts/check_guardrails.sh
python3.11 tools/agent/preview_csv.py data.csv --cols case_id,gate_status,reason --grep blocked --rows 20
python3.11 tools/agent/package_brief.py work_products/2026-07/2026-07-22/example --rows 1
python3.11 tools/agent/gate_snapshot.py work_products/2026-07/2026-07-22/example --limit 8
python3.11 tools/agent/manifest_check.py imports/2026-07-22_example.json --check-paths
python3.11 tools/agent/closeout_stub.py --task-id TODO-EXAMPLE-2026-07-22
```

Rules:

- Use `safe_rg.py` instead of bare repo-wide `rg`; broad `.` searches require
  `--allow-broad` and still stop at `--max-lines`.
- Use `status_scope.py`; do not run full `git status --short` in this dirty
  workspace unless explicitly diagnosing repo-wide state.
- Use `guardrail_summary.py` for validators that print long claim-boundary or
  lint hit lists; rerun the raw command only when the summary reports a failure
  or the task requires detailed review.
- Use `preview_csv.py` for evidence tables; select columns and a row limit.
- Use `package_brief.py` before recursive package inspection; escalate to
  individual files only after the brief identifies what matters.
- Use `gate_snapshot.py` on gate/audit packages before opening their full CSVs;
  it reports compact decision, pass/blocker, guardrail, and next-action rows.
- Use `manifest_check.py` for JSON validation; do not pretty-print full
  manifests unless reviewing content.
- Use `closeout_stub.py` in dry-run mode to confirm standard status, journal,
  and manifest paths; use `--write` only when those paths are owned by the
  board row.

## `link_report.py`

Dry-run default:

```bash
python3.11 tools/agent/link_report.py reports/2026-07/2026-07-22/example/README.md \
  --title "Example report"
```

Explicit write:

```bash
python3.11 tools/agent/link_report.py reports/2026-07/2026-07-22/example/README.md \
  --title "Example report" --targets start,maps,litrev,forward,thesis --write
```

This helper is intentionally simple. Review its diff after use and adjust the
wording when a report needs a more specific pointer.

## `board_archive.py`

```bash
python3.11 tools/agent/board_archive.py
python3.11 tools/agent/board_archive.py --apply
python3.11 tools/agent/board_archive.py --archive-task <TASK_ID> --apply
python3.11 tools/agent/board_archive.py --check
```

Default mode is a dry run. `--apply` moves every `## Archived ...` section from
`.agent/BOARD.md` to `.agent/BOARD_ARCHIVE.md`, preserving parser-readable rows
verbatim and leaving a short archive pointer on the live board. `--archive-task`
moves one `STATUS: COMPLETE` or `STATUS: BLOCKED` live row directly into the
archive after validation. `--check` fails if archive sections are still embedded
in the live board.

`finish_task.py` is archive-aware, so completed tasks remain discoverable after
their rows move out of `.agent/BOARD.md`.

## `background_compute_helper.py`

```bash
python3.11 tools/agent/background_compute_helper.py --duration long --openfoam --persistent
python3.11 tools/agent/background_compute_helper.py --duration short --openfoam --host-kind compute
```

Recommendations:

- long or persistent work: `sbatch` from a login node;
- compute work inside allocation: `srun`;
- `tmux` only preserves launcher/session state and does not allocate resources.

Every background handoff must include task ID, job/step ID, node, exact command,
log path, expected completion/cleanup condition, and whether killing tmux or the
allocation is safe.

For long or convergence-driven jobs, use the principal/monitor pattern:

- The principal agent owns the science task, prepares and launches the job, then
  stays responsive to the user.
- The monitor agent owns a separate read-only board row and periodically checks
  `squeue`, `sacct`, logs, process state, and expected output files.
- `tmux` is acceptable for a background terminal, but the monitor handoff must
  name the tmux session and safe-kill behavior.
- The monitor must not submit duplicate jobs, cancel/requeue, harvest, admit,
  or fit unless those actions are explicitly scoped in its board row.

## `split_policy_lint.py`

```bash
python3.11 tools/agent/split_policy_lint.py operational_notes .agent/BOARD.md
```

Flags stale final-predictive split language such as Salt2-train /
Salt3-validation / Salt4-holdout unless the line clearly marks it as historical,
superseded, previous, diagnostic, development-only, or a completed archival
board row.

Current policy: canonical final predictive training spans Salt1-4; testing and
holdout come from perturbation, external, and new-CFD rows.

## `runtime_input_lint.py`

```bash
python3.11 tools/agent/runtime_input_lint.py <package-or-doc>
```

Flags lines that appear to use forbidden predictive runtime inputs:

- CFD `mdot`;
- realized `wallHeatFlux`;
- imposed CFD cooler duty;
- validation or holdout temperatures;
- target sensor values as model inputs.

The linter allows explicit guardrail language such as "must not use",
"forbidden", "scoring-only", or "diagnostic". It is heuristic; review findings
before editing scientific claims.

## `case_schema_lint.py`

```bash
python3.11 tools/agent/case_schema_lint.py <package-or-doc>
python3.11 tools/agent/case_schema_lint.py <package-or-doc> --json
```

Checks whether a package appears to carry the CFD-to-1D postprocessing schema:

- BC/source/material roles;
- geometry/material mapping;
- patchwise heat ledger;
- pressure ladder;
- thermal score rows;
- sensor targets;
- runtime-input audit;
- PM5/F6/internal-Nu rows;
- admission table.

Passing this tool means the schema lanes are present by text coverage. It does
not mean the row is scientifically admitted.

## Maintenance Notes

- Keep tools stdlib-only unless the repo already has a hard dependency.
- Keep default behavior read-only.
- Add tests in `tools/agent/test_agent_tools.py` for every parser or policy
  change.
- Do not make these tools mutate native CFD outputs, registry state, scheduler
  state, or external Fluid files.
