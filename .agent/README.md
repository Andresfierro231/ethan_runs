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

## Files here

- `BOARD.md`: active tasks, backlog, blocked work, and review queue
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
