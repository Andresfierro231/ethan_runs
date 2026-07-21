---
provenance:
  - .agent/BOARD.md
  - tools/extract/render_branch_velocity_arrow_images.py
  - tools/extract/2026-06-15_paraview_field_render_workflow.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_upcomer_orthogonal_arrow_render/README.md
  - figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/png/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows_side_x.png
tags: [journal, thesis, upcomer, paraview, figures]
related:
  - .agent/status/2026-07-21_TODO-THESIS-UPCOMER-ORTHOGONAL-ARROW-RENDER-2026-07-21.md
  - imports/2026-07-21_thesis_upcomer_orthogonal_arrow_render.json
task: TODO-THESIS-UPCOMER-ORTHOGONAL-ARROW-RENDER-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Thesis Upcomer Orthogonal Arrow Render

## Attempted

Extended the existing ParaView branch velocity-arrow renderer with explicit
view presets so the current front-view camera can be reproduced and a side view
normal to `x` can be generated without overwriting the existing output tree.

## Observed

The current durable Salt4 upcomer arrow image looks normal to `z` and slices at
the reference `z` plane. The new `side_x` preset slices at the reference `x`
plane and views normal to `x`, which gives a side-on orthogonal projection of
the upcomer.

The first Slurm attempt, `3308604`, failed because `plane_span` compared a
float against a list. After fixing the helper, Slurm job `3308608` completed
successfully and wrote PNG/SVG/PDF assets. The raw `pvbatch` log still contains
the known ParaView post-write segmentation fault, but the scheduler wrapper
validated the written status JSON and required image files before exiting
successfully.

## Inferred

The generated `side_x` image is useful as a thesis companion view when a reader
needs to see that the front-view upcomer arrow evidence was not a single camera
artifact. It remains diagnostic visualization evidence only.

## Caveats

- The side projection is narrow because the upcomer geometry itself is narrow
  in the `z` direction relative to its vertical span.
- This render does not add exchange-QOI data and does not admit an upcomer
  closure.
- Salt2 and Salt3 orthogonal views can now be rendered with the same preset,
  but this task produced only the requested Salt4 upcomer view.

## Next Useful Actions

1. If the thesis needs a side-by-side panel, render `side_x` for `val_salt2`
   using the same script and output tree.
2. If the side view is too narrow for print, rerun with a larger
   `--camera-scale-factor` or a cropped figure layout, preserving the status
   JSON and output manifest.
3. Use SVG as the thesis source and PDF as the fallback.
