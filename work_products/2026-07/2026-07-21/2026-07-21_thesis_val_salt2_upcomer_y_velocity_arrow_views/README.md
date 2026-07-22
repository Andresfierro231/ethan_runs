---
provenance:
  - tools/extract/render_branch_velocity_arrow_images.py
  - staging/render_inputs/val_salt_test_2_coarse_mesh_laminar/reconstructed_case/val_salt_test_2_coarse_mesh_laminar.foam
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_y_velocity_arrow_views/output_manifest.csv
tags: [thesis, cfd-pp, figures, paraview, upcomer, recirculation, val-salt2, y-velocity]
related:
  - TODO-THESIS-VAL-SALT2-UPCOMER-Y-VELOCITY-ARROW-VIEWS-2026-07-21
  - TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
task: TODO-THESIS-VAL-SALT2-UPCOMER-Y-VELOCITY-ARROW-VIEWS-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: work-product
status: complete
supersedes: []
superseded_by:
---
# Salt2 Validation Upcomer Y-Velocity Arrow Views

## Purpose

This package renders the Salt2 validation/external upcomer using only the
y-velocity component, rather than velocity magnitude. The intent is to show
vertical throughflow direction explicitly after the magnitude arrows proved
visually ambiguous for some side views.

The renderer mode is:

- arrow vector: `U_y*jHat`
- glyph length: `abs(U_y)`
- color field: signed `U_y`
- colorbar: `Y velocity [m/s]`

These figures are qualitative diagnostic CFD visuals. They do not admit
ordinary upcomer `Nu`, `f_D`, component `K`, exchange-cell coefficients, or
final predictive scores.

## Source And Runtime

- Source ID: `val_salt_test_2_coarse_mesh_laminar`
- Case ID: `salt_test_2`
- Component: `upcomer`
- Staged reader input:
  `staging/render_inputs/val_salt_test_2_coarse_mesh_laminar/reconstructed_case/val_salt_test_2_coarse_mesh_laminar.foam`
- Rendered time: `1724.0 s`
- Slurm job: `3308809`
- Node: `c318-009.ls6.tacc.utexas.edu`
- Script:
  `scripts/render_val_salt2_upcomer_y_velocity_side_views.sbatch`
- Output root:
  `figures/figures_rendered/paraview_velocity_y_arrows/`

## Outputs

| View | SVG | Use note |
| --- | --- | --- |
| `side_x` | `figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_y_component_arrows_side_x.svg` | Clear y-direction view; slender because the upcomer is viewed normal to `x`. |
| `side_neg_x` | `figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_y_component_arrows_side_neg_x.svg` | Opposite x-side companion; also slender. |
| `side_y` | `figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_y_component_arrows_side_y.svg` | Less intuitive because the selected y-direction arrows point mostly along the camera axis and appear as circular arrow ends. |
| `side_z` | `figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_y_component_arrows_side_z.svg` | Useful for a front/side vertical-flow reading with visible up/down arrow direction. |

PNG and PDF siblings exist under the same `png/` and `pdf/` directories with
matching basenames.

## Validation

- `python3.11 -m py_compile tools/extract/render_branch_velocity_arrow_images.py`
  passed.
- `bash -n scripts/render_val_salt2_upcomer_y_velocity_side_views.sbatch`
  passed.
- Slurm job `3308809` reported `COMPLETED|0:0`.
- The wrapper validated all `12` requested PNG/SVG/PDF artifacts.
- Visual sanity checks confirmed all four PNGs are nonblank and labeled as
  `y-velocity component arrows`.

ParaView/OSMesa returned post-write `rc=255` signal-11 messages for `side_x`,
`side_neg_x`, and `side_y`, but each status JSON reports `status: rendered`,
all formats exist, and the wrapper validation passed.

## Guardrails

- No native OpenFOAM source outputs were mutated.
- No registry or admission state was changed.
- No OpenFOAM solver or postprocessing harvest was launched.
- No Fluid/external repository files were edited.
- No fitting, tuning, closure admission, SAM validation, or final predictive
  score claim was made.
- The Salt2 validation/external row remains diagnostic/test evidence only.
