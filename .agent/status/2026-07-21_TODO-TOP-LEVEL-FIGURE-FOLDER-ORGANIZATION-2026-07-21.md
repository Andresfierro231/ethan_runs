---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/pre_move_figures_file_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/pre_move_root_figures_rendered_file_manifest.csv
tags: [status, cleanup, figures, work-products, provenance, symlink]
related:
  - TODO-TOP-LEVEL-FIGURE-FOLDER-ORGANIZATION-2026-07-21
  - .agent/journal/2026-07-21/top-level-figure-folder-organization.md
  - work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/README.md
task: TODO-TOP-LEVEL-FIGURE-FOLDER-ORGANIZATION-2026-07-21
date: 2026-07-21
role: Cleaner/Figures/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-TOP-LEVEL-FIGURE-FOLDER-ORGANIZATION-2026-07-21

## Objective

Organize root-level generated figure folders so durable content lives under a
dated work-products package, while preserving existing references where needed.

## Outcome

Complete. The physical `figures/` and `figures_rendered/` directories were
relocated under:

```text
work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/legacy_roots/
```

The repository-root paths now exist only as compatibility symlinks:

```text
figures -> work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/legacy_roots/figures
figures_rendered -> work_products/2026-07/2026-07-21/2026-07-21_top_level_figure_folder_organization/legacy_roots/figures_rendered
```

## Changes Made

- Wrote pre-move file manifests for root `figures/` and `figures_rendered/`.
- Moved physical root `figures/` into the dated work-products package.
- Moved physical root `figures_rendered/` into the dated work-products package.
- Created compatibility symlinks at root `figures` and `figures_rendered`.
- Wrote post-move symlink-resolution manifests.
- Added package README, status, journal, import manifest, and board completion
  text.

## Validation

- `git ls-files figures_rendered figures` returned no tracked files.
- `figures_rendered/` inventory before move: `2` files, `44K`.
- `figures/` inventory before move: `659` files, `2.1G`.
- `test -f figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_y_component_arrows_side_z.svg`
  passed through the compatibility symlink.
- `test -f figures_rendered/viscosity_screening_salt_test_1_kirst_coarse_mesh/overview.png`
  passed through the compatibility symlink.
- Post-move manifests were generated through `find -L` for both symlink paths.

## Unresolved Blockers

None for this cleanup. Future figure-generation scripts should prefer task-owned
dated `work_products/<date>/<package>/figures/` outputs. The root symlinks are
kept only for compatibility with existing provenance and scripts.

## Guardrails

- Native OpenFOAM source outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- OpenFOAM solver/postprocessing/sampler/harvest launched: no.
- Fluid/external repository mutation: no.
- Fitting/tuning/model selection/admission/final score claim: no.
- Runtime-leakage rules changed: no.
- Figure pixels manually edited: no.
