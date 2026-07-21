# Documentation Frontmatter Schema

Reviewed: `2026-07-13` (AGENT-294)

This schema makes the repo's ~1000 markdown docs machine-queryable so that
`tools/docs/build_repo_index.py` can generate an always-current `STATE.md`,
`catalog.json/csv`, and `BLOCKERS.md` instead of relying on hand-maintained
summaries that go stale. It binds **both Claude and Codex, who work as
teammates on one shared corpus** — there is no per-document "owner". Attribution
and traceability come from `task` (and the git history), not authorship, so
either teammate can pick up, extend, or correct any doc.

## Priority order

The three highest-value fields — the ones that make continuity and report-writing
work — are, in order:

1. **`provenance`** — the exact file paths a doc's claims rest on. Cite files, not
   chat. This is what makes reports assemble-able (a report section = a join over
   `catalog.json` + each package's `summary.json`).
2. **`tags`** — stable topic tags. This is what makes past material findable and
   powers the topic maps and `STATE.md`'s per-tag index.
3. **`related`** — sibling docs in the same thread, so the chain of work is
   navigable without grep.

Everything else is bookkeeping. Fill these three on every durable doc even when
you skip the rest.

## Rule

Every **new** durable markdown artifact — status file, journal entry, operational
note, report `README.md`, and work_product `README.md` — SHOULD begin with a YAML
frontmatter block. It is a small, additive extension of the existing §9
conventions. Backfill of old docs is optional; the generator tolerates docs
without frontmatter by inferring from filename + conventional lines.

## Block

```yaml
---
# --- priority core (fill these first) ---
provenance:                # exact repo-relative paths this doc's claims rest on
  - work_products/2026-07/2026-07-13/.../summary.json
tags: [doc-continuity, provenance, tooling]   # stable topic tags (no leading '#')
related:                   # sibling docs in the same thread
  - operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md
# --- bookkeeping ---
task: AGENT-294            # task ID for traceability (AGENT-NNN, T#, F#, TODO-SLUG)
date: 2026-07-13           # ISO date the work was done
role: Coordinator/Writer   # function performed (not a person / not an owner)
type: journal              # journal | status | operational_note | report | work_product | map
status: complete           # active | blocked | complete | superseded | reference
# --- supersession (anti-stale) ---
supersedes: []             # doc paths or task IDs this OVERTURNS
superseded_by:             # set later if THIS doc is overturned; then flip status: superseded
---
```

## Field notes

- **No `owner`.** Docs are shared team artifacts. Use `task` for traceability. The
  only place a live "who is holding this" marker belongs is the `.agent/BOARD.md`
  Owner column, which is a conflict-avoidance lock on an *active* task, not a
  claim of authorship over the resulting docs.
- **`status`** drives `STATE.md`. `blocked` feeds the blocker sweep; `complete`
  and `superseded` are excluded from "open work."
- **`supersedes` / `superseded_by`** are the anti-stale mechanism. When a finding
  overturns an earlier one, name the earlier doc/task and set the earlier doc's
  `status: superseded`. This prevents solved problems from being re-reported as
  open (the exact failure AGENT-289 documented).
- **`tags`** should reuse existing stable tags where possible (see the topic hubs
  in `operational_notes/maps/`). Prefer a small controlled vocabulary.

## Blockers register

Blockers do NOT live scattered in journals. Each distinct blocker gets one entry
in `.agent/blockers.yml` (curated, structured). The generator renders it to
`.agent/BLOCKERS.md` and validates it (`--check`): evidence path must exist, an
`open` blocker may not also carry `superseded_by`/`resolved_by`, and every open
blocker must carry a `last_reviewed` date.

## Related

- `.agent/blockers.yml`
- `tools/docs/build_repo_index.py`
- `operational_notes/maps/README.md`
- `AGENTS.md` (Documentation continuity protocol)
- `CLAUDE.md` §9
