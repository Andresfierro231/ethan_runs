---
provenance:
  - AGENTS.md
  - .agent/README.md
  - operational_notes/START_HERE_FOR_AGENTS.md
  - operational_notes/maps/agent-operations.md
  - tools/agent/
tags: [agent-operations, coordination, tooling, start-here]
related:
  - .agent/status/2026-07-17_AGENT-489.md
  - .agent/journal/2026-07-17/agent-user-efficiency-platform.md
  - imports/2026-07-17_agent_user_efficiency_platform.json
task: AGENT-489
date: 2026-07-17
role: Coordinator/Implementer/Tester/Writer
type: operational_note
status: complete
---
# 2026-07-17 Agent/User Efficiency Platform

## Why This Exists

The repo now has enough board rows, dated work products, topic maps, and
scheduler handoffs that agents were spending time rediscovering the operating
model. This package turns the repeated conventions into one start-here page,
one topic map, and small read-only tools.

## Open First

- `operational_notes/START_HERE_FOR_AGENTS.md`
- `operational_notes/maps/agent-operations.md`
- `.agent/README.md`
- `AGENTS.md`
- `tools/agent/`

## Added Capabilities

- `preflight_task.py` checks board scope and active edit-path conflicts.
- `finish_task.py` validates task handoff artifacts and blocker-index checks.
- `new_task.py` scaffolds task artifacts in dry-run or explicit-write mode.
- `split_policy_lint.py` catches stale current split language.
- `runtime_input_lint.py` catches possible predictive runtime-input leakage.
- `case_schema_lint.py` checks CFD-to-1D schema-lane coverage.
- `background_compute_helper.py` recommends `sbatch`, `srun`, or `tmux+srun`.
- `board_dashboard.py` prints a compact active/TODO board view.

## Guardrails

- Tools are stdlib-only and read-only by default.
- `finish_task.py --rebuild-index` is explicit opt-in.
- No native CFD outputs, scheduler state, registry/admission state, or external
  Fluid files are touched.
- Generated index refresh is deferred because active AGENT-482 owns
  `.agent/STATE.md`, `.agent/BLOCKERS.md`, `.agent/catalog.json`, and
  `.agent/catalog.csv`.

## Next Useful Improvements

- After AGENT-482 releases generated-index ownership, run
  `python3.11 tools/docs/build_repo_index.py` and then
  `python3.11 tools/agent/finish_task.py --task-id AGENT-489`.
- Use `case_schema_lint.py` as an advisory precheck for Salt1 schema promotion,
  Salt2 +/-5Q holdout repair, and `val_salt2` external-test ledgers.
- Consider adding CI-like wrappers later if this repo gets a formal test gate.

