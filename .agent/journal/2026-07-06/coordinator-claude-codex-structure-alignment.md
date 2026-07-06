# Coordinator: Claude–Codex Output Structure Alignment

Date: `2026-07-06`
Role: Coordinator
Task: ad-hoc (no BOARD claim needed — coordination/documentation only)
Owner: claude

---

## Task

User requested that all Claude work and documentation use the same folder/file
structure as Codex so the repo is organized for good communication and synergy.

## Files Inspected

- `AGENTS.md` — non-negotiable rules, manifest requirements
- `.agent/BOARD.md` — active task format and ownership
- `.agent/FILE_OWNERSHIP.md` — path ownership map
- `.agent/ROLES.md` — role definitions
- `.agent/journal/README.md` — journal entry requirements
- `.agent/status/2026-07-04_AGENT-178.md` (Codex reference)
- `.agent/status/2026-07-01_AGENT-162.md` (Claude reference)
- `.agent/journal/2026-07-04/salt-perturbation-quarantine-and-corrected-relaunch.md` (Codex)
- `.agent/journal/2026-07-04/coordinator-monday-handoff-and-claude-bootstrap.md` (Claude)
- `reports/2026-07/2026-07-01/2026-07-01_rom_postprocessing_correctness_validation/` (Codex — has summary.json)
- `reports/2026-06/2026-06-30/2026-06-30_claude_closure_results/` (Claude — missing summary.json)
- `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/` (Claude — missing summary.json)
- `reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/` (Claude — missing summary.json)
- `imports/` directory (Codex creates per-session JSONs; Claude was missing July ones)

## Gap Analysis

Five structural misalignments found between Claude and Codex outputs:

### 1. Status file headers
- **Codex**: `# AGENT-NNN Status` (title case); `Role:` field; sections `## Scope / ## Completed / ## Current State / ## Follow-up`
- **Claude**: lowercase heading; `Task:` instead of `Role:`; ad-hoc sections (`## Done`, etc.)
- **Fix**: documented correct format in CLAUDE.md §9.1

### 2. work_products naming
- **Codex June**: `2026-06-29_ethan_*`; **Codex July**: plain `YYYY-MM-DD_slug`
- **Claude June**: `2026-06-30_claude_*` (owner-prefixed — divergence)
- **Claude July**: already using plain `YYYY-MM-DD_slug` — aligned
- **Fix**: documented in CLAUDE.md §9.3; June entries keep existing names (renaming would break provenance references)

### 3. imports JSON manifests
- **Codex**: creates `imports/YYYY-MM-DD_*.json` for every major session
- **Claude**: created one (June 30) but nothing for July sessions
- **Fix**: created retroactive manifest for AGENT-179 (July 4) at `imports/2026-07-04_friction_closures_and_claude_bootstrap.json`; documented requirement in CLAUDE.md §9.4

### 4. Report packages missing summary.json
- **Codex**: every package has `README.md` + `summary.json`
- **Claude July**: `2026-07-01_model_form_comparison` and `2026-07-02_overnight_synthesis` had only `README.md`
- **Fix**: added `summary.json` to both packages
- Note: June 2026 Claude reports left as-is (already cited in journals/journals; retroactive change would create provenance inconsistency)

### 5. Journal entry completeness
- Both agents follow the same `role-slug.md` naming; some Claude entries lacked exact file lists / command records
- **Fix**: documented required fields in CLAUDE.md §9.2; no retroactive edits to existing entries

## Files Changed

- `CLAUDE.md` — added §9 "File output conventions — must match Codex" (6 subsections: status files, journal entries, work_products naming, imports JSON, report packages, BOARD claims)
- `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/summary.json` — created
- `reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/summary.json` — created
- `imports/2026-07-04_friction_closures_and_claude_bootstrap.json` — created

## Commands Run

None (documentation/metadata work only; no scripts executed).

## Results

- CLAUDE.md now explicitly documents the 6 file-output conventions Claude must follow to stay aligned with Codex
- Two Claude July report packages now have `summary.json` (consistent with Codex standard)
- AGENT-179's July 4 work now has an import manifest
- Going forward: any new Claude task must (1) create `imports/YYYY-MM-DD_*.json`, (2) write `README.md + summary.json` in every report package, (3) use `YYYY-MM-DD_slug` (no `_claude_` prefix) for work_products, (4) follow the Codex-standard status file format

## Incomplete Lines of Investigation

- June 2026 Claude report packages still lack `summary.json` (`2026-06-30_claude_action_items_summary`, `2026-06-30_claude_closure_results`). These are complete work products already cited in journals and reports. Left without retroactive summary.json to avoid provenance inconsistency; the gap is acceptable given those packages are complete.
- The AGENT-171 (July 2, overnight) work referenced by `2026-07-02_overnight_synthesis` does have a proper report summary now added.

## Next Steps

Future Claude sessions should start by reading CLAUDE.md §9 alongside the startup protocol to ensure all outputs conform to the shared structure.
