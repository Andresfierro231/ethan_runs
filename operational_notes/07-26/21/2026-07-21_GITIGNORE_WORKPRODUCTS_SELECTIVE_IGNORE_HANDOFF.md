---
provenance:
  - .gitignore
  - .agent/status/2026-07-21_TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21.md
  - .agent/journal/2026-07-21/gitignore-workproducts-selective-ignore-handoff.md
tags: [cleanup, gitignore, work-products, tomorrow-handoff]
related:
  - imports/2026-07-21_gitignore_workproducts_selective_ignore_handoff.json
task: TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21
date: 2026-07-21
role: Cleaner/Coordinator/Writer
type: operational_note
status: complete
---
# Start Here Tomorrow: Work Products Gitignore Hygiene

Task: `TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21`

## Why This Exists

The repo needed safer `git add` behavior after a large cleanup/staging discussion. The initial instinct to ignore all of `work_products/*` was wrong because `work_products` contains durable evidence packages. The policy now keeps useful package artifacts visible while hiding raw/generated heavy payloads.

## Files To Open First

- `.gitignore`
- `.agent/status/2026-07-21_TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21.md`
- `.agent/journal/2026-07-21/gitignore-workproducts-selective-ignore-handoff.md`
- `imports/2026-07-21_gitignore_workproducts_selective_ignore_handoff.json`

## Current Policy

Visible under `work_products`: `*.md`, `*.json`, `*.csv`, `*.svg`, `*.png`, `*.pdf`, `*.txt`, `*.yaml`, `*.yml`, and `*.pptx`.

Ignored under `work_products`: caches/bytecode, VTK/OGV/STL, `recon/`, `repair_trial_output/recon/`, large cell-volume/mask/face CSV dumps, seeded geometry/source row dumps, sampled interface fields, sampled wall/core temperature rows, sampled pressure detail rows, trusted-wall wallHeatFlux detail rows, `legacy_roots/figures`, and generated `figures/**/pdf/*.pdf` exports.

## Progress

- `.gitignore` has been updated.
- No files were deleted, moved, staged, committed, or pushed.
- `work_products` content was inspected but not mutated.
- The broad dirty worktree remains and includes unrelated active/completed agent outputs.

## Validation Snapshot

- `work_products` total inspected size: about `40G`.
- Total files observed before filtering: `8117`.
- Visible untracked `work_products` files after filtering: `5830`.
- Largest visible files after filtering: mostly `1.3M` to `5.2M` SVG/CSV/PPTX artifacts.
- Spot checks showed useful docs/summaries visible and raw sampled/generated PDF payloads ignored.

## Tomorrow's Next Steps

1. Review `.gitignore` for policy intent and whether `work_products/**/figures/**/pdf/*.pdf` is too broad for any curated PDF use case.
2. Run `git status --short -- .gitignore work_products figures figures_rendered scratchpad registry reports`.
3. Stage `.gitignore` and this handoff set as one cleanup/documentation group if the diff still looks right.
4. Do not stage all visible `work_products` directories wholesale. Inspect package-level intent first.
5. If another large generated family appears, add a narrow generator-specific rule and validate with `git check-ignore -v`.

## Do Not Do

- Do not restore blanket `work_products/*`.
- Do not delete `work_products`, `figures`, `figures_rendered`, registry outputs, or scratch trees without an explicit dry-run inventory and user approval.
- Do not stage unrelated active-agent files into the ignore-policy commit.
- Do not mutate native CFD/OpenFOAM outputs, registry/admission state, scheduler jobs, Fluid, or external repositories.
