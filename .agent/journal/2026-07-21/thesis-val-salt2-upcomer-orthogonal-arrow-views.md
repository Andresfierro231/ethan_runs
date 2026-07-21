---
provenance:
  - figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_orthogonal_arrow_views/README.md
tags: [journal, thesis, figures, upcomer, recirculation, val-salt2]
related:
  - TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21
task: TODO-THESIS-VAL-SALT2-UPCOMER-ORTHOGONAL-ARROW-VIEWS-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Salt2 Validation Upcomer Orthogonal Arrow Views

## Attempted

The user identified the existing Salt2 validation/external upcomer velocity-arrow
SVG as a preferred visual and requested the other page-aligned views from
`side_x`, `side_y`, and `side_z`. I opened a narrow board row, extended the
existing ParaView renderer with explicit `side_y` and `side_z` presets, and
submitted a task-owned Slurm render job.

## Observed

- Source figure:
  `figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg`
- Renderer source ID: `val_salt_test_2_coarse_mesh_laminar`
- Component: `upcomer`
- Rendered time: `1724.0 s`
- Slurm job: `3308677`
- Scheduler result: `COMPLETED|0:0`
- Output validation: `9` non-empty PNG/SVG/PDF artifacts.
- Visual checks:
  - `side_x` is nonblank and page-aligned but thin, as expected for an
    orthogonal projection normal to `x`.
  - `side_y` is nonblank, page-aligned, and gives the clearest horizontal
    loop-head view.
  - `side_z` is nonblank and page-aligned, preserving the original/front axis
    convention under the requested suffix.

## Inferred

For thesis layout, `side_y` should be the first Salt2 orthogonal companion if a
single additional panel is used. `side_x` and `side_z` remain useful as a full
view-family record, but `side_x` has less visual area and `side_z` overlaps
more with the existing front-view axis convention.

## Contradictions Or Caveats

ParaView/OSMesa returned post-write signal-11 messages for `side_x` and
`side_z`. The generated status JSON for each view reports `status: rendered`,
the wrapper validated all files, and manual visual inspection confirmed the
PNGs are usable. This is a runtime caveat, not a failed figure artifact.

The Salt2 validation/external case must remain diagnostic/test evidence. These
figures do not train a closure, admit upcomer `Nu/f_D/K`, admit exchange-cell
coefficients, or support final predictive-score claims.

## Next Useful Actions

- Use the new `side_y` SVG as the preferred additional Salt2 upcomer side-view
  panel in F-03A if the thesis needs one page-aligned loop-head companion.
- If the final thesis build wants local copies rather than direct paths, open a
  separate figure-packaging row to copy/export only the selected panels.
- Keep any recirculation-fraction or exchange-QOI quantification in the S13/S14
  study rows; do not infer those values from these qualitative arrow images.
