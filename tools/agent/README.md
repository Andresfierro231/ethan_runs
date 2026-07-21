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
| `board_dashboard.py` | anytime | Print compact active/live agent and open TODO view. |
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
