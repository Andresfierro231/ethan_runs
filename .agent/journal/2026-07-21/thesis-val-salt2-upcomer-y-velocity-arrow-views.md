---
provenance:
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_y_velocity_arrow_views/README.md
tags: [journal, thesis, figures, upcomer, recirculation, val-salt2, y-velocity]
related:
  - TODO-THESIS-VAL-SALT2-UPCOMER-Y-VELOCITY-ARROW-VIEWS-2026-07-21
task: TODO-THESIS-VAL-SALT2-UPCOMER-Y-VELOCITY-ARROW-VIEWS-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Salt2 Validation Upcomer Y-Velocity Arrow Views

## Attempted

The user clarified that the problem with the previous side views was not just
camera direction; they wanted a figure set showing the y-direction velocity
component rather than velocity magnitude. I extended the renderer with a
non-default y-component mode and generated four Salt2 validation/external
upcomer views: `side_x`, `side_neg_x`, `side_y`, and `side_z`.

## Observed

- Source ID: `val_salt_test_2_coarse_mesh_laminar`
- Component: `upcomer`
- Velocity mode: `y_component`
- Render definition: arrow vector `U_y*jHat`, glyph scale `abs(U_y)`, color
  field signed `U_y`
- Rendered time: `1724.0 s`
- Slurm job: `3308809`
- Scheduler result: `COMPLETED|0:0`
- Output validation: `12` non-empty PNG/SVG/PDF artifacts.
- Visual checks:
  - `side_x` and `side_neg_x` are nonblank, slender, and dominated by positive
    y-direction arrows.
  - `side_y` is nonblank but shows many circular glyph ends because y-directed
    arrows point mostly along the camera axis.
  - `side_z` is nonblank and reads clearly as up/down y-component motion.

## Inferred

For thesis layout, use `side_z` or one of the x-normal views when the goal is to
show vertical y-throughflow direction. Use `side_y` only with an explicit camera
caveat, or keep it as a supporting/generated artifact rather than the primary
panel.

## Contradictions Or Caveats

ParaView/OSMesa again returned post-write signal-11 messages for some views.
The status files reported `rendered`, the wrapper validated the artifacts, and
the PNGs passed visual inspection.

The y-component views are still diagnostic Salt2 validation/external evidence.
They do not train a closure, admit ordinary upcomer `Nu/f_D/K`, admit
exchange-cell coefficients, or support a final predictive score.

## Next Useful Actions

- Prefer `side_z` for a single `U_y` thesis panel.
- Keep the magnitude and `U_y` view families separate in captions.
- Do not infer recirculation fraction or exchange QOIs from these images; those
  remain dedicated S13/S14 study outputs.
