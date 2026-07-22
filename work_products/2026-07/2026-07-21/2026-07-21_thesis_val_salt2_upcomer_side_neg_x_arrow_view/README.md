---
provenance:
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_orthogonal_arrow_views/README.md
  - staging/render_inputs/val_salt_test_2_coarse_mesh_laminar/reconstructed_case/val_salt_test_2_coarse_mesh_laminar.foam
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_side_neg_x_arrow_view/output_manifest.csv
tags: [thesis, cfd-pp, figures, paraview, upcomer, recirculation, val-salt2]
related:
  - TODO-THESIS-VAL-SALT2-UPCOMER-SIDE-NEG-X-ARROW-VIEW-2026-07-21
  - TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
task: TODO-THESIS-VAL-SALT2-UPCOMER-SIDE-NEG-X-ARROW-VIEW-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: work-product
status: complete
supersedes: []
superseded_by:
---
# Salt2 Validation Upcomer Opposite X-Side Arrow View

## Purpose

This package renders the opposite camera side of the Salt2 validation/external
upcomer `side_x` velocity-arrow view. The new view uses the existing renderer
preset `side_neg_x`, which keeps the same x-normal slice basis and reverses the
camera direction.

## Source And Runtime

- Source ID: `val_salt_test_2_coarse_mesh_laminar`
- Case ID: `salt_test_2`
- Component: `upcomer`
- View preset and output suffix: `side_neg_x`
- Staged reader input:
  `staging/render_inputs/val_salt_test_2_coarse_mesh_laminar/reconstructed_case/val_salt_test_2_coarse_mesh_laminar.foam`
- Rendered time: `1724.0 s`
- Slurm job: `3308713`
- Node: `c318-009.ls6.tacc.utexas.edu`
- Script:
  `scripts/render_val_salt2_upcomer_side_neg_x.sbatch`

## Outputs

| Format | Path |
| --- | --- |
| PNG | `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/png/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_neg_x.png` |
| SVG | `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_neg_x.svg` |
| PDF | `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/pdf/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_neg_x.pdf` |

The image is nonblank and page-aligned. As with `side_x`, it is a slender
projection because the upcomer is viewed normal to the x direction. For a broad
horizontal loop-head panel, prefer the existing `side_y` view from the companion
orthogonal-view package.

## Validation

- `bash -n scripts/render_val_salt2_upcomer_side_neg_x.sbatch` passed.
- Slurm job `3308713` reported `COMPLETED|0:0`.
- The wrapper validated all `3` requested artifacts in `output_manifest.csv`.
- Visual sanity check confirmed the PNG is nonblank, page-aligned, and includes
  the title, timestamp, arrows, and colorbar.

ParaView/OSMesa returned a post-write `pvbatch_exit=255` with a signal-11
message after the files were written. The status payload reports
`status: rendered`, all formats are present and non-empty, and visual inspection
passed.

## Guardrails

- No native OpenFOAM source outputs were mutated.
- No registry or admission state was changed.
- No renderer code was edited for this follow-on view.
- No OpenFOAM solver or postprocessing harvest was launched.
- No Fluid/external repository files were edited.
- No fitting, tuning, closure admission, SAM validation, or final predictive
  score claim was made.
- The Salt2 validation/external row remains diagnostic/test evidence only.
