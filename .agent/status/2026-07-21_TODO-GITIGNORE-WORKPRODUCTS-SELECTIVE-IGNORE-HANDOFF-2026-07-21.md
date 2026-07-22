---
provenance:
  - .gitignore
  - .agent/BOARD.md
tags: [cleanup, gitignore, work-products, handoff]
related:
  - .agent/journal/2026-07-21/gitignore-workproducts-selective-ignore-handoff.md
  - operational_notes/07-26/21/2026-07-21_GITIGNORE_WORKPRODUCTS_SELECTIVE_IGNORE_HANDOFF.md
task: TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21
date: 2026-07-21
role: Cleaner/Coordinator/Writer
type: status
status: complete
---
# TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21 Status

Task: `TODO-GITIGNORE-WORKPRODUCTS-SELECTIVE-IGNORE-HANDOFF-2026-07-21`

## Changes Made

- Replaced the prior blanket `work_products/*` ignore with recursive selective rules.
- Kept normal durable package artifacts visible: Markdown, JSON, CSV, SVG, PNG, PDF, TXT, YAML/YML, and PPTX.
- Added targeted ignores for heavy/generated `work_products` payloads: `.pytest_cache`, bytecode, VTK/OGV/STL files, reconstructed solver trees, repair-trial reconstructed trees, large cell-volume/mask/face row dumps, seeded geometry/source row dumps, sampled interface fields, sampled wall/core temperature rows, sampled pressure detail rows, trusted-wall wallHeatFlux detail rows, duplicated `legacy_roots/figures`, and generated `figures/**/pdf/*.pdf` fan-outs.
- Preserved the earlier local hygiene ignores for `figures_rendered`, generated registry products, selected large report profile CSVs, `scratchpad`, and compiled `jadyn_runs/**/runtime_libs/*.so`.
- Added this status file, journal entry, import manifest, operational handoff, and completed board row.

## Validation

- `find work_products -type f | wc -l` before targeted filtering showed `8117` files.
- `du -sh work_products` showed the tree is about `40G`, dominated by regenerated/reconstructed solver and render payloads.
- `git ls-files -o --exclude-standard work_products | wc -l` after the final policy returned `5830`, leaving durable package outputs visible instead of hiding the whole tree.
- Largest visible `work_products` files after filtering were mostly `1.3M` to `5.2M` SVG/CSV/PPTX artifacts, not 25 MB generated PDF fan-outs or 100 MB to multi-GB solver files.
- `git check-ignore -v` spot checks confirmed:
  - `README.md`, `summary.json`, and small CSV package summaries are unignored by allowlist rules.
  - generated legacy/render PDF outputs are ignored by `work_products/**/legacy_roots/figures/` and `work_products/**/figures/**/pdf/*.pdf`.
  - raw sampled/detail field dumps such as `sampled_interface_fields.csv`, `sampled_pressure_detail.csv`, and `trusted_wall_wallHeatFlux_detail.csv` are ignored by targeted row-dump rules.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- `work_products/**` file contents mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/sampler/harvest launch: no.
- Fluid/external repository edit: no.
- Blocker-register source change: no.
- Files deleted, moved, reverted, staged, committed, or pushed: no.
- Broader dirty worktree cleaned: no; many unrelated modified/untracked files remain from other active/completed agents and must be staged only by logical ownership groups.
