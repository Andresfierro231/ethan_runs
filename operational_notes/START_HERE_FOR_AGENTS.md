---
provenance:
  - AGENTS.md
  - .agent/README.md
  - .agent/BOARD.md
  - .agent/STATE.md
  - operational_notes/maps/README.md
  - tools/agent/
tags: [agent-operations, start-here, coordination, tooling]
related:
  - operational_notes/maps/agent-operations.md
  - .agent/README.md
  - .agent/DOC_FRONTMATTER_SCHEMA.md
task: AGENT-489
date: 2026-07-17
role: Coordinator/Writer
type: operational_note
status: reference
---
# Start Here for Agents and New Users

This is the first human-readable entry point for working in `ethan_runs/`.
Generated state files and topic maps remain authoritative when they disagree
with older prose.

## Open First

1. `AGENTS.md`
2. `.agent/BOARD.md`
3. `.agent/FILE_OWNERSHIP.md`
4. `.agent/ROLES.md`
5. `.agent/STATE.md`
6. `.agent/BLOCKERS.md`
7. `operational_notes/maps/README.md`

For a focused research thread, open the matching topic map before grepping old
work products. For active predictive-model work, start with
`operational_notes/maps/forward-predictive-model.md` and
`operational_notes/maps/cfd-runs-and-admission.md`.

Current Monday 2026-07-20 fresh-agent handoff:
`operational_notes/07-26/17/2026-07-17_MONDAY_MORNING_FRESH_AGENT_HANDOFF.md`.
Open it immediately after the standard board/state files before submitting,
harvesting, admitting, or launching new forward-model, PM10/high-heat, or
corrected-Q work. It records the latest Friday scheduler state, no-duplicate job
rules, terminal harvest triggers, and the recommended UMX1 upcomer
mixing/stratification next-model path.

Saturday 2026-07-18 addendum for Monday source/property and dispatch:
`operational_notes/07-26/18/2026-07-18_MONDAY_SOURCE_PROPERTY_AND_AGENT_DISPATCH.md`.
Open it before assigning new scorecard/admission work. It records the
source/property label enforcement gate, Monday task packets, structure rules to
prevent blank fit/admission labels, and the current recommendation not to launch
additional weekend jobs beyond the already-running queue.

## Before Editing

- Claim or confirm a board row.
- Confirm allowed edit paths and read-only context.
- Do not edit files owned by another active row.
- Run:

```bash
python3.11 tools/agent/preflight_task.py --task-id <TASK_ID>
```

If the preflight reports conflicts, stop and coordinate before editing.

## Background Compute Policy

- Use `sbatch` from a login node for durable long or overnight work.
- Use `srun` for compute work inside an allocation.
- Use `tmux` only to keep an interactive launcher/session alive.
- Never run heavy solver, rendering, or full-case extraction work on login
  nodes.
- Handoffs must record task ID, job/step ID, node, exact command, log path,
  cleanup condition, and whether killing tmux/allocation is safe.

Use the principal-agent plus monitor-agent pattern for long or
convergence-driven work:

- The principal agent owns the science, launches the job, writes the running
  handoff, and stays available for user coordination.
- The monitor agent owns a separate narrow read-only board row and periodically
  checks `squeue`, `sacct`, logs, process state, and expected outputs.
- A background terminal may be left running, but its task ID, session name,
  node, command, logs, and safe-kill/cancel rules must be documented before the
  principal agent moves on.
- The monitor must not submit duplicates, harvest, admit, cancel, or requeue
  unless the board row explicitly allows that action.

Use:

```bash
python3.11 tools/agent/background_compute_helper.py --duration long --openfoam --persistent
```

## Before Finishing

Write or update:

- `.agent/status/<date>_<TASK_ID>.md`
- `.agent/journal/<date>/<slug>.md`
- `imports/<date>_<slug>.json`
- a work-product README or operational note if the task produced durable
  research context

Then run:

```bash
python3.11 tools/agent/finish_task.py --task-id <TASK_ID>
```

For significant sessions, regenerate the docs index unless another active board
row owns `.agent/STATE.md`, `.agent/BLOCKERS.md`, `.agent/catalog.json`, and
`.agent/catalog.csv`.

## Full Documentation Contract

Do not mark a task complete until another agent can answer these questions from
durable files:

- What was the objective and final outcome?
- Which files changed and which files were only read?
- What commands/tests/checks were run, and what were the results?
- What evidence supports any scientific or policy claim?
- What was not done, and what remains blocked or risky?
- Were native CFD outputs, registry rows, scheduler state, generated index
  files, or external repositories mutated?
- What should the next agent open first?

`finish_task.py` checks the minimum shape: status, journal, import manifest,
manifest changed-file paths, read-only context, mutation flags, and blocker-index
validation. Passing the tool does not replace scientific review; it prevents
undocumented handoffs.

## Common Guardrails

- Native CFD outputs are read-only unless a board row explicitly claims staged
  copies or controlled postprocessing outputs.
- Registry and scheduler mutation require explicit scope.
- Predictive model artifacts must not use CFD `mdot`, realized `wallHeatFlux`,
  imposed CFD cooler duty, validation temperatures, or holdout temperatures as
  runtime inputs.
- Stale split language must be marked historical or superseded. Canonical final
  predictive training now spans Salt1-4; holdout/testing comes from
  perturbation, external, and new-CFD rows.

## Helpful Commands

```bash
python3.11 tools/agent/board_dashboard.py
python3.11 tools/agent/split_policy_lint.py operational_notes .agent/BOARD.md
python3.11 tools/agent/runtime_input_lint.py <package-or-doc>
python3.11 tools/agent/case_schema_lint.py <work-product-or-package>
python3.11 tools/docs/build_repo_index.py --check
```
