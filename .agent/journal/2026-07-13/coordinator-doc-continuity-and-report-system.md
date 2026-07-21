---
provenance:
  - tools/docs/build_repo_index.py
  - .agent/DOC_FRONTMATTER_SCHEMA.md
  - .agent/blockers.yml
  - operational_notes/maps/README.md
tags: [doc-continuity, provenance, tags, research-index, tooling, blocker-register, map-of-content, teammates]
related:
  - operational_notes/maps/README.md
  - .agent/STATE.md
  - .agent/BLOCKERS.md
  - operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md
task: AGENT-294
date: 2026-07-13
role: Coordinator/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
---
# Documentation Continuity & Report-Generation System

Task: `AGENT-294`
Role: Coordinator / Implementer / Tester / Writer

## Why (problem)

The repo is information-rich but retrieval-poor: ~974 durable markdown docs, and
until now **0 had machine-readable frontmatter**. Discovery was grep-only, and
continuity depended on hand-maintained summaries (`CLAUDE.md`, MASTER TODO) that
go stale — which is exactly how AGENT-289 found three solved blockers still being
reported as open. Fix: make the corpus queryable + add a generated freshness
layer that cannot drift, and give each research thread a canonical hub.

## What was built

1. **Frontmatter schema** — `.agent/DOC_FRONTMATTER_SCHEMA.md`. A small additive
   YAML header for new docs. Priority core (fill first): **provenance, tags,
   related**. No per-doc `owner` — Claude and Codex are teammates on one corpus;
   traceability is via `task`.
2. **Index generator** — `tools/docs/build_repo_index.py` (+ self-contained
   `test_build_repo_index.py`, 10 tests, no pytest dependency). Scans status,
   journal, operational_notes, report READMEs, work_product READMEs, and the
   maps; frontmatter-aware with filename+conventional-line fallback for legacy
   docs. Emits:
   - `.agent/STATE.md` — generated current state: corpus counts, priority-field
     coverage, open blockers, active board tasks, recent activity, latest doc per
     tag. Points to the human START_HERE handoff.
   - `.agent/catalog.json` / `.agent/catalog.csv` — every doc as a queryable
     record (tags/provenance/related front-and-centre).
   - `.agent/BLOCKERS.md` — rendered from the register.
   - `--check` mode: the automatable no-stale-blocker guard.
3. **Blocker register** — `.agent/blockers.yml`, seeded from the AGENT-289 audit
   (7 open frontier blockers + 3 resolved/superseded kept so they are NOT
   re-reported). Validated: evidence path must exist; an `open` blocker may not
   also claim resolved/superseded; `superseded_by` must resolve to a known id.
4. **Topic maps** — `operational_notes/maps/` with a README index and 9 living
   map-of-content hubs (friction-closures, thermal-closures-and-internal-nu,
   mesh-gci-and-uncertainty, forward-predictive-model, cfd-runs-and-admission,
   pressure-and-momentum-budget, geometry-and-mesh-truth,
   thermal-boundary-and-radiation, literature-synthesis-and-gates). Each is the
   canonical entry point to its thread with trusted results, open/blocked items
   (by blocker id), avenues tried with outcomes, and canonical artifacts.
5. **Binding cross-agent rule** — added to `AGENTS.md` ("Documentation continuity
   and index protocol") and `CLAUDE.md` §9.0.

## Mid-course correction (user)

User directed: "remove the owner thing — Codex and Claude work as teammates" and
"prioritize provenance, tags, related docs." Applied:
- Dropped `owner` from the frontmatter schema, all 10 map docs (`sed` strip), and
  the generator's record/catalog/STATE outputs. Kept the BOARD `Owner` column
  only as the live active-task lock (flagged the distinction in the schema).
- Elevated provenance/tags/related to the schema's "priority core", added them as
  leading catalog columns, and added a priority-field coverage section to
  `STATE.md`.

## Files inspected

`AGENTS.md`, `CLAUDE.md`, `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`,
`.agent/ROLES.md`, `.agent/DECISIONS.md`,
`operational_notes/07-26/13/2026-07-13_CURRENT_CLOSURE_AND_PREDICTIVE_MODEL_START_HERE.md`,
and (via the map subagents) the friction / thermal / mesh / forward-model /
runs / pressure / geometry / radiation / litrev package READMEs.

## Files changed

- NEW `tools/docs/build_repo_index.py`, `tools/docs/test_build_repo_index.py`
- NEW `.agent/DOC_FRONTMATTER_SCHEMA.md`, `.agent/blockers.yml`
- NEW generated: `.agent/STATE.md`, `.agent/catalog.json`, `.agent/catalog.csv`, `.agent/BLOCKERS.md`
- NEW `operational_notes/maps/README.md` + 9 topic hubs
- Additive sections in `AGENTS.md` and `CLAUDE.md` §9.0
- `.agent/BOARD.md` (own AGENT-294 row), `.agent/status/2026-07-13_AGENT-294.md`,
  `imports/2026-07-13_doc_continuity_system.json`

## Commands run (reproducible)

```bash
python3 tools/docs/test_build_repo_index.py     # 10 passed
python3 tools/docs/build_repo_index.py --check   # blocker register OK (10 entries)
python3 tools/docs/build_repo_index.py           # indexed 974 docs; 105 board rows; 10 blockers
```

## Results / observations

- 974 docs indexed; 10 maps typed correctly; the tag index surfaces the correct
  latest doc per topic (e.g. `external-boundary` → the radiation hub).
- Priority-field coverage is honestly low today (tags ~2%, provenance frontmatter
  0%, related ~1%) because only the new AGENT-294 docs use the schema. This is the
  intended baseline metric; it rises as frontmatter adoption grows. The maps carry
  provenance richly in-body (link lists) even though they express it there rather
  than in a frontmatter `provenance:` list.

## Coordination note

Discovered and resolved a task-ID collision: Codex concurrently claimed AGENT-293;
this task renumbered to AGENT-294. (The generator would now surface such a
collision in the board scan.)

## Incomplete / next steps

- Optional: a git pre-commit or nightly hook to auto-run the generator (not
  installed without approval).
- Optional backfill: add frontmatter to high-traffic legacy docs to raise
  coverage; the generator already tolerates their absence.
- Consider giving the maps a frontmatter `provenance:` list (currently in-body).

## Related

- `operational_notes/maps/README.md`
- `.agent/DOC_FRONTMATTER_SCHEMA.md`
- `.agent/STATE.md`
- `.agent/BLOCKERS.md`
- `operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md`
