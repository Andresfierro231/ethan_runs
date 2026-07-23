---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_agent_token_efficiency_missing_tools/source_manifest.csv
tags: [journal, agent-tooling, token-efficiency]
related:
  - .agent/status/2026-07-22_TODO-AGENT-TOKEN-EFFICIENCY-MISSING-TOOLS-2026-07-22.md
  - imports/2026-07-22_agent_token_efficiency_missing_tools.json
task: TODO-AGENT-TOKEN-EFFICIENCY-MISSING-TOOLS-2026-07-22
date: 2026-07-22
role: Coordinator / Implementer / Tester / Writer
type: journal
status: complete
---
# Agent Token Efficiency Missing Tools

## Attempted

Audited the token-efficiency recommendations against the current repo. The
existing tooling already covered exact board slices, task context, package
briefs, safe bounded `rg`, CSV previews, manifest checks, closeout stubs,
guardrail summaries, and bounded git diffs. The missing pieces were compact
live-blocker reporting and a scope-conflict audit for stale broad board claims.

## Observed

`live_blockers.py` reduces blocker startup context to the generated open table:
ID, severity, blocked lane, reviewed date, and optional evidence path.

`scope_conflict_audit.py` caught the live issue that repeatedly caused preflight
waste: the trigger-gated S11 row has broad `tools/analyze/` ownership, which
conflicts with narrow active analysis files. It also reports the current
`.agent/BLOCKERS.md` overlap between two trigger-gated CSEM writer rows.

## Inferred

The largest remaining avoidable token use is not lack of package-summary tools;
those already exist. The more important failure mode is stale broad board scope
and agents repeatedly discovering that conflict through failed preflights. The
new audit makes that visible in one bounded command.

## Caveats

`scope_conflict_audit.py` exits `1` when live conflicts exist. That is intended
for CI-like or preflight use. Its output is bounded by `--limit` and should be
treated as coordination signal, not as an instruction to edit another active
row without owning it.

## Next Useful Actions

1. Narrow or remove the trigger-gated S11 optional `tools/analyze/` claim when a
   coordinator row is available.
2. Prefer `live_blockers.py` over reading full blocker notes unless the exact
   blocker evidence must be inspected.
3. Use `scope_conflict_audit.py` before creating new analysis rows to avoid
   repeated preflight failures and duplicate package-only workarounds.
