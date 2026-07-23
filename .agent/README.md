# Agent Coordination

This directory is the shared coordination layer for Codex agents working in
`ethan_runs/`.

## Launching agents

From repo root:

```bash
bash .agent/scripts/agent_context.sh
```

From any subfolder:

```bash
bash "$(git rev-parse --show-toplevel)/.agent/scripts/agent_context.sh"
```

If `git rev-parse --show-toplevel` is unavailable, run:

```bash
bash ../../.agent/scripts/agent_context.sh
```

after navigating upward to the repo root candidate.

## Startup checklist

1. Find repo root.
2. Read `AGENTS.md`.
3. Read `.agent/BOARD.md`.
4. Read `.agent/FILE_OWNERSHIP.md`.
5. Identify role and task ID.
6. Confirm allowed edit paths.
7. Work only on assigned scope.
8. Update status, journal, or handoff before stopping.

`agent_context.sh` now also prints local instruction files between the current
directory and repo root, including `AGENTS.override.md`, `README.md`, and
`TODO.md` when present.

## Agent efficiency helpers

Start from `operational_notes/START_HERE_FOR_AGENTS.md` for the current
operator/user-facing workflow.

Useful read-only checks live under `tools/agent/`:

- `preflight_task.py --task-id <TASK>`: summarize scope, conflicts, and handoff
  requirements before editing.
- `finish_task.py --task-id <TASK>`: validate status/journal/import/index
  handoff before closing a task.
- `board_summary.py --limit 30`: bounded live-board summary for routine
  coordinator scans.
- `board_slice.py --task-id <TASK>`: print one exact board row or a small
  query-filtered slice without dumping long scope text.
- `task_context.py --task-id <TASK>`: show allowed edit paths, read-only
  context, conflicts, instruction files, and closeout artifact presence.
- `board_archive.py --apply && board_archive.py --check`: move historical
  archived sections into `.agent/BOARD_ARCHIVE.md`.
- `board_dashboard.py`: compact view of active/live rows and open TODOs.
- `package_brief.py <path> --rows 1`: summarize package files, CSV headers,
  row counts, scalar JSON, and README headings before detailed inspection.
- `closeout_stub.py --task-id <TASK>`: dry-run or write status/journal/import
  skeletons for scoped closeout.
- `../docs/state_brief.py --active --blockers`: compact current-state and
  blocker view from generated docs.
- `split_policy_lint.py`: catch stale final-predictive split language.
- `case_schema_lint.py`: check CFD-to-1D postprocessing schema coverage.
- `runtime_input_lint.py`: catch possible predictive runtime-input leakage.
- `guardrail_summary.py -- <command>`: summarize noisy guardrail/lint output
  into bounded PASS/FAIL/NOTE lines before rerunning verbose checks.
- `background_compute_helper.py`: recommend `sbatch`, `srun`, or `tmux+srun`
  and list required handoff fields.

Full documentation minimum before closeout:

- status file with objective/outcome, changed artifacts, validation, unresolved
  blockers, and guardrails;
- journal entry with observations, interpretation, caveats, and next actions;
- import manifest with changed files, read-only context, and mutation flags;
- package README or operational note for durable research/tooling changes.

Background compute policy:

- durable long work: `sbatch` from a login node;
- compute work inside an allocation: `srun`;
- session persistence only: `tmux`;
- no expensive login-node runs.
- for long or convergence-driven jobs, split the work:
  - principal agent launches and documents the job, then stays available for
    user coordination;
  - monitor agent claims a separate read-only row and watches `squeue`,
    `sacct`, logs, process state, and expected outputs;
  - monitor agents do not submit duplicates, cancel, requeue, harvest, or admit
    unless their board row explicitly allows it.

See `tools/agent/README.md` for complete tool usage and failure semantics.

Low-token default sequence for a known task:

```bash
python3.11 tools/agent/board_slice.py --task-id <TASK>
python3.11 tools/agent/task_context.py --task-id <TASK>
python3.11 tools/docs/state_brief.py --active --blockers
```

For evidence packages, run `package_brief.py` before opening whole CSV, JSON,
or README files. Keep raw board/status/CSV dumps for cases where the bounded
helpers show that detailed inspection is necessary.

For git-heavy cleanup and staging, prefer bounded summaries:

```bash
python3.11 tools/git/clean_status_summary.py --untracked all --limit 30
python3.11 tools/git/staged_audit.py --limit 20
python3.11 tools/git/diff_check_filtered.py --max-output-lines 80
python3.11 tools/git/diff_summary.py --mode unstaged --limit 40 -- <owned paths>
```

## Files here

- `BOARD.md`: active tasks, backlog, blocked work, and review queue
- `BOARD_ARCHIVE.md`: historical archived board sections
- `FILE_OWNERSHIP.md`: editable path rules and shared files
- `ROLES.md`: agent role definitions
- `DECISIONS.md`: durable coordination decisions
- `JOURNAL_POLICY.md`: raw and curated journal rules
- `CLEANUP_POLICY.md`: cleanup safety protocol
- `status/`: short task status notes
- `journal/`: raw append-only per-day agent logs
- `handoffs/`: concise task handoffs
- `cleanup/`: dry-run cleanup inventories and action logs
- `locks/`: optional lightweight file/task lock notes
