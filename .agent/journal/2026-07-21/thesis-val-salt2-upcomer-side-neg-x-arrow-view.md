---
provenance:
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_side_neg_x_arrow_view/README.md
tags: [journal, thesis, figures, upcomer, recirculation, val-salt2]
related:
  - TODO-THESIS-VAL-SALT2-UPCOMER-SIDE-NEG-X-ARROW-VIEW-2026-07-21
task: TODO-THESIS-VAL-SALT2-UPCOMER-SIDE-NEG-X-ARROW-VIEW-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Salt2 Validation Upcomer Opposite X-Side Arrow View

## Attempted

The user asked whether the other side of the `side_x` Salt2 validation/external
upcomer arrow view could be generated. I used the existing `side_neg_x` renderer
preset, which reverses the camera direction for the x-normal view without
editing the renderer.

## Observed

- Source ID: `val_salt_test_2_coarse_mesh_laminar`
- Component: `upcomer`
- View preset and suffix: `side_neg_x`
- Rendered time: `1724.0 s`
- Slurm job: `3308713`
- Scheduler result: `COMPLETED|0:0`
- Output validation: `3` non-empty PNG/SVG/PDF artifacts.
- Visual check: the PNG is nonblank, page-aligned, and shows the reverse
  x-normal side of the upcomer relative to `side_x`.

## Inferred

The `side_neg_x` view is a legitimate opposite-side companion to `side_x`, but
both x-normal views remain slender because the upcomer geometry is narrow from
that camera direction. If the thesis needs a single broad loop-head panel, the
existing `side_y` view is still the better first choice.

## Contradictions Or Caveats

ParaView/OSMesa returned a post-write signal-11 message and `pvbatch_exit=255`.
The renderer status reports `rendered`, the wrapper validated all artifacts, and
the visual sanity check passed, so this is recorded as a runtime caveat rather
than a failed figure.

The figure remains diagnostic Salt2 validation/external evidence only. It does
not train or admit any ordinary upcomer `Nu/f_D/K`, exchange-cell coefficient,
or predictive score.

## Next Useful Actions

- Use `side_neg_x` only when the thesis needs the explicit reverse x-normal
  view.
- Use `side_y` first when the layout needs one visually broad side panel.
- Keep recirculation quantification in the dedicated S13/S14 evidence rows,
  not in qualitative arrow-image interpretation.
