---
provenance:
  - AGENTS.md
  - .agent/README.md
  - operational_notes/START_HERE_FOR_AGENTS.md
  - tools/agent/README.md
  - tools/agent/finish_task.py
tags: [agent-operations, documentation, tooling, handoff]
related:
  - .agent/status/2026-07-17_AGENT-491.md
  - .agent/journal/2026-07-17/agent-documentation-enforcement-and-tool-docs.md
  - imports/2026-07-17_agent_documentation_enforcement_and_tool_docs.json
task: AGENT-491
date: 2026-07-17
role: Coordinator/Implementer/Tester/Writer
type: operational_note
status: complete
---
# 2026-07-17 Agent Documentation Enforcement and Tool Docs

## Why This Exists

The user asked that agents always fully document everything they do, and that
the new `tools/agent` helpers be thoroughly documented. This task turns the
documentation expectation from a convention into a checkable closeout contract.

## What Changed

- `AGENTS.md` now has a full documentation contract.
- `.agent/README.md` and `operational_notes/START_HERE_FOR_AGENTS.md` now state
  the minimum closeout documentation requirements.
- `tools/agent/README.md` documents every agent helper, expected usage, exit
  behavior, limitations, and maintenance rules.
- `tools/agent/finish_task.py` now checks that status files contain changes,
  validation, and guardrails; journals name the task and are not empty stubs;
  import manifests include changed files, read-only context, and mutation flags.

## Required Agent Closeout Shape

Before a task is marked complete or blocked, another agent should be able to
open durable files and answer:

- objective and outcome;
- changed files and read-only context;
- validation commands and results;
- evidence behind scientific or policy claims;
- unresolved blockers and next actions;
- mutation status for native CFD outputs, registry/admission state, scheduler
  state, generated index files, and external repos.

## Validation

Focused tests for `tools/agent` passed after adding the stricter validation
rules. The final AGENT-491 status records the exact commands.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, solver jobs,
or external Fluid files were mutated.

