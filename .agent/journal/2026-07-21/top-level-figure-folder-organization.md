---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/pre_move_figures_file_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/pre_move_root_figures_rendered_file_manifest.csv
tags: [journal, cleanup, figures, work-products, provenance, symlink]
related:
  - TODO-TOP-LEVEL-FIGURE-FOLDER-ORGANIZATION-2026-07-21
  - .agent/status/2026-07-21_TODO-TOP-LEVEL-FIGURE-FOLDER-ORGANIZATION-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/README.md
task: TODO-TOP-LEVEL-FIGURE-FOLDER-ORGANIZATION-2026-07-21
date: 2026-07-21
role: Cleaner/Figures/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Top-Level Figure Folder Organization

## Attempted

The user identified the root `figures_rendered/` folder as apparently unused and
not worth keeping, and asked that the root `figures/` folder be organized under
today's `work_products/` tree rather than left hanging from the repository root.
I audited both folders, then moved their physical storage under a dated cleanup
package and preserved top-level compatibility paths as symlinks.

## Observed

- `figures_rendered/` was `44K` and contained two files from a legacy Kirst
  overview validation.
- `figures/` was `2.1G` and contained `659` files, mostly under
  `figures/figures_rendered/`.
- `git ls-files figures_rendered figures` returned no tracked files.
- Recent thesis and figure-package docs refer to `figures/figures_rendered/...`,
  so deleting or moving `figures/` without a symlink would have broken
  provenance.

## Inferred

`figures_rendered/` is legacy provenance, not an active root output location.
`figures/` is generated-artifact state that should no longer be physically
root-owned, but it still needs the old path as a compatibility interface for
existing manifests and scripts.

## Actions

- Moved physical `figures/` to
  `work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/legacy_roots/figures/`.
- Moved physical `figures_rendered/` to
  `work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/legacy_roots/figures_rendered/`.
- Created root symlinks `figures` and `figures_rendered` to those relocated
  directories.
- Wrote pre-move and post-move resolution manifests.

## Contradictions Or Caveats

The root paths still exist as symlinks. This is intentional: it satisfies the
storage organization goal while preventing existing docs, import manifests, and
scripts from breaking immediately. Future cleanup can update old references and
then remove the compatibility symlinks if desired.

## Next Useful Actions

- Update new render scripts to default to dated `work_products/.../figures/`
  output roots.
- Avoid adding new physical top-level generated artifact folders.
- Only remove compatibility symlinks after references to `figures/...` and
  `figures_rendered/...` have been migrated or explicitly accepted as stale.
