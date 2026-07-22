---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/pre_move_figures_file_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/pre_move_root_figures_rendered_file_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/post_move_figures_symlink_resolution_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/post_move_root_figures_rendered_symlink_resolution_manifest.csv
tags: [cleanup, figures, work-products, provenance, symlink]
related:
  - TODO-TOP-LEVEL-FIGURE-FOLDER-ORGANIZATION-2026-07-21
  - .agent/status/2026-07-21_TODO-TOP-LEVEL-FIGURE-FOLDER-ORGANIZATION-2026-07-21.md
  - .agent/journal/2026-07-21/top-level-figure-folder-organization.md
task: TODO-TOP-LEVEL-FIGURE-FOLDER-ORGANIZATION-2026-07-21
date: 2026-07-21
role: Cleaner/Figures/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Top-Level Figure Folder Organization

## Purpose

The user requested cleanup of two top-level generated-artifact paths:

- `figures_rendered/`, which appeared unused and not worth keeping as a root
  directory.
- `figures/`, which should not physically hang from the repository root when
  dated `work_products/` packages are the preferred durable home.

This package relocates both physical directories under a dated work-product
archive while preserving compatibility for existing path references.

## Layout After Cleanup

Physical storage now lives here:

```text
work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/legacy_roots/figures/
work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/legacy_roots/figures_rendered/
```

The root paths are compatibility symlinks:

```text
figures -> work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/legacy_roots/figures
figures_rendered -> work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/legacy_roots/figures_rendered
```

This keeps existing references such as `figures/figures_rendered/...` working
while putting the data under the dated package requested by the user.

## Inventory

Pre-move inventories:

- `pre_move_figures_file_manifest.csv`: `659` files.
- `pre_move_root_figures_rendered_file_manifest.csv`: `2` files.

Post-move symlink-resolution inventories:

- `post_move_figures_symlink_resolution_manifest.csv`: should match the `659`
  file count through `figures`.
- `post_move_root_figures_rendered_symlink_resolution_manifest.csv`: should
  match the `2` file count through `figures_rendered`.

Size check after relocation:

- Physical `legacy_roots/figures`: `2.1G`.
- Physical `legacy_roots/figures_rendered`: `44K`.
- Root compatibility symlink `figures`: `512` bytes.
- Root compatibility symlink `figures_rendered`: `512` bytes.

## Interpretation

The old root `figures_rendered/` contained only:

- `figures_rendered/viscosity_screening_salt_test_1_kirst_coarse_mesh/overview.png`
- `figures_rendered/viscosity_screening_salt_test_1_kirst_coarse_mesh/status.json`

It is legacy validation/provenance material, not a current figure production
root. It is archived here and exposed through a symlink only for old references.

The old root `figures/` was not safe to delete or move without compatibility,
because recent thesis packages and import manifests refer to
`figures/figures_rendered/...`. It is now physically organized under this dated
work product, with the old path preserved as a compatibility symlink.

## Guardrails

- Native OpenFOAM source outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- OpenFOAM solver/postprocessing/sampler/harvest launched: no.
- Fluid/external repository mutation: no.
- Fitting/tuning/model selection/admission/final score claim: no.
- Runtime-leakage rules changed: no.
- Figure pixels manually edited: no.
