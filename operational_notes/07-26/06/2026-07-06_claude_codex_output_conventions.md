# Claude–Codex Output Conventions (locked 2026-07-06)

This note records the output conventions that both Claude and Codex must follow
to keep the repo organized for shared communication and handoff.

## File conventions (6 rules)

### 1. Status files (`.agent/status/YYYY-MM-DD_AGENT-NNN.md`)
```
# AGENT-NNN Status
Date: `YYYY-MM-DD`
Role: Coordinator / Implementer / Writer
Owner: <claude|codex>
## Scope
## Completed
## Current State
## Follow-up
```

### 2. Journal entries (`.agent/journal/YYYY-MM-DD/role-slug.md`)
Required fields: date, role, task ID, files inspected, files changed, commands run,
results/observations, incomplete investigations, next steps.

### 3. work_products naming
`YYYY-MM-DD_descriptive-slug` — no `_claude_` or `_codex_` owner prefix.
(June 2026 `_claude_` entries are grandfathered; do not rename.)

### 4. imports JSON (`imports/YYYY-MM-DD_slug.json`)
Required for every major session. Minimum keys: `manifest_id`, `owner`, `task`,
`generated_at`, `purpose`, `scope`, `new_tools`, `work_products`.

### 5. Report packages
Every package = `README.md` + `summary.json`. A README-only package is incomplete.
`summary.json` minimum: `generated_at`, `task`, `inputs`, `outputs`, `limitations`.

### 6. BOARD.md claims
Claim a row before editing any shared file. Use specific path claims, not broad wildcards.

## operational_notes path structure
`operational_notes/MM-YY/DD/YYYY-MM-DD_slug.md`
Example: July 6, 2026 → `operational_notes/07-26/06/2026-07-06_*.md`

## Gap history (what was fixed 2026-07-06)
- CLAUDE.md updated with §9 (file output conventions)
- `summary.json` added to two Claude July report packages that were missing it
- Import manifest created for AGENT-179 (July 4 work)
- See `.agent/journal/2026-07-06/coordinator-claude-codex-structure-alignment.md`
