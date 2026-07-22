---
provenance:
  - tools/extract/render_branch_velocity_arrow_images.py
  - figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg
  - staging/render_inputs/val_salt_test_2_coarse_mesh_laminar/reconstructed_case/val_salt_test_2_coarse_mesh_laminar.foam
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_orthogonal_arrow_views/output_manifest.csv
tags: [thesis, cfd-pp, figures, paraview, upcomer, recirculation, val-salt2]
related:
  - TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
task: TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: work-product
status: complete
supersedes: []
superseded_by:
---
# Salt2 Validation Upcomer Orthogonal Arrow Views

## Purpose

This package renders the requested `side_x`, `side_y`, and `side_z` companions
to the liked Salt2 validation/external upcomer velocity-arrow figure:

```text
figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg
```

The figures are diagnostic CFD visuals for upcomer model-form discussion. They
may support the thesis argument that ordinary single-stream and 2D-axisymmetric
upcomer closures are not adequate in recirculating regimes. They do not admit an
ordinary upcomer `Nu`, `f_D`, component `K`, exchange-cell coefficient, or final
predictive score.

## Source And Runtime

- Source ID: `val_salt_test_2_coarse_mesh_laminar`
- Case ID: `salt_test_2`
- Staged reader input:
  `staging/render_inputs/val_salt_test_2_coarse_mesh_laminar/reconstructed_case/val_salt_test_2_coarse_mesh_laminar.foam`
- Native source root recorded by the renderer:
  `/scratch/09748/andresfierro231/projects_scratch/val_salt_test_2_coarse_mesh_laminar`
- Rendered time: `1724.0 s`
- Slurm job: `3308677`
- Node: `c318-009.ls6.tacc.utexas.edu`
- Script:
  `scripts/render_val_salt2_upcomer_side_xyz.sbatch`
- Renderer:
  `tools/extract/render_branch_velocity_arrow_images.py`

## Outputs

The wrapper wrote `output_manifest.csv` and validated all nine requested
artifacts.

| View | Recommended use | SVG |
| --- | --- | --- |
| `side_x` | Thin orthogonal projection normal to `x`; useful as a camera-normal companion, less visually rich than `side_y`. | `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_x.svg` |
| `side_y` | Clearest page-aligned horizontal loop-head view; use first if only one new Salt2 side view is needed. | `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_y.svg` |
| `side_z` | Requested `side_z` suffix with the original/front axis convention; visually close to the existing front-view orientation. | `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_z.svg` |

PNG and PDF siblings exist under the same `png/` and `pdf/` directories with
matching basenames.

## Validation

- `python3.11 -m py_compile tools/extract/render_branch_velocity_arrow_images.py`
  passed.
- `bash -n scripts/render_val_salt2_upcomer_side_xyz.sbatch` passed.
- `git diff --check` on the renderer, board row, and Slurm script passed.
- Slurm job `3308677` completed with `COMPLETED|0:0`.
- The wrapper validated `9` non-empty PNG/SVG/PDF artifacts.
- Visual sanity checks confirmed `side_x`, `side_y`, and `side_z` PNGs are
  nonblank, page-aligned, and include the title, timestamp, arrows, and colorbar.

ParaView/OSMesa returned post-write signal-11 messages for `side_x` and
`side_z`, but each corresponding status JSON reports `status: rendered`, all
three formats exist, and the wrapper validation passed. Treat that as a render
runtime caveat, not as a failed artifact.

## Guardrails

- No native OpenFOAM source outputs were mutated.
- No registry or admission state was changed.
- No OpenFOAM solver or postprocessing harvest was launched.
- No Fluid/external repository files were edited.
- No fitting, tuning, closure admission, SAM validation, or final predictive
  score claim was made.
- The Salt2 validation/external row remains diagnostic/test evidence only.
