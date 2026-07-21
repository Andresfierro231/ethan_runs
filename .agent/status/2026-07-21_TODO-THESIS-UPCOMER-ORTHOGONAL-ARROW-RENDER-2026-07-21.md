---
provenance:
  - .agent/BOARD.md
  - tools/extract/render_branch_velocity_arrow_images.py
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_upcomer_orthogonal_arrow_render/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_upcomer_orthogonal_arrow_render/salt4_upcomer_side_x_status.json
  - figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/png/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows_side_x.png
tags: [status, thesis, upcomer, paraview, figures]
related:
  - .agent/journal/2026-07-21/thesis-upcomer-orthogonal-arrow-render.md
  - imports/2026-07-21_thesis_upcomer_orthogonal_arrow_render.json
task: TODO-THESIS-UPCOMER-ORTHOGONAL-ARROW-RENDER-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-THESIS-UPCOMER-ORTHOGONAL-ARROW-RENDER-2026-07-21

## Objective

Create a new upcomer velocity-arrow image from a camera direction normal to the
existing front-view Salt4 upcomer arrow image, without overwriting existing
front-view assets or changing scientific admission state.

## Changes Made

- Added `side_x`, `side_neg_x`, and `top_y` view presets to
  `tools/extract/render_branch_velocity_arrow_images.py`.
- Added task-owned Slurm wrapper:
  `work_products/2026-07/2026-07-21/2026-07-21_thesis_upcomer_orthogonal_arrow_render/scripts/render_salt4_upcomer_side_x.sbatch`.
- Rendered Salt4 Jin upcomer side-view PNG/SVG/PDF under:
  `figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/`.
- Added work-product README and output manifest.
- Updated thesis figure ledgers so F-03A includes the new Salt4 `side_x`
  orthogonal view.

## Validation

- `python3.11 -m py_compile tools/extract/render_branch_velocity_arrow_images.py`: passed.
- `bash -n .../render_salt4_upcomer_side_x.sbatch`: passed.
- `git diff --check -- <task paths>`: passed before scheduler submission and
  will be rerun at closeout.
- Slurm job `3308604`: failed before output because of a `plane_span` helper
  bug; no figure outputs were accepted from that attempt.
- Slurm job `3308608`: completed `0:0` on `NuclearEnergy-dev`.
- Render status: `rendered_count=1`, `failed_count=0`.
- PNG/SVG/PDF output files exist.
- Visual sanity check: PNG is nonblank, side-on, titled, and colorbar-present.

## Guardrails

- Native CFD/OpenFOAM outputs: not modified.
- Existing front-view figure assets: not overwritten.
- Registry/admission state: not modified.
- Scheduler action: task-owned ParaView render job only.
- OpenFOAM solver/postprocessing, sampler, and harvest: not run.
- Fluid/external repos: not modified.
- Fitting, tuning, model selection, closure admission, final score, and SAM
  validation: not performed.
- Runtime leakage policy unchanged.
