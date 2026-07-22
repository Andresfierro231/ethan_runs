---
provenance:
  - tools/extract/render_branch_velocity_arrow_images.py
  - tools/extract/2026-06-15_paraview_field_render_workflow.md
  - figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/status.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_upcomer_orthogonal_arrow_render/salt4_upcomer_side_x_status.json
  - figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/png/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows_side_x.png
tags: [thesis, upcomer, recirculation, paraview, figures]
related:
  - operational_notes/07-26/21/2026-07-21_THESIS_UPCOMER_RECIRCULATION_VISUAL_EVIDENCE_INSERTION.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
task: TODO-THESIS-UPCOMER-ORTHOGONAL-ARROW-RENDER-2026-07-21
date: 2026-07-21
role: Figures/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis Upcomer Orthogonal Arrow Render

## Result

Created a Salt4 Jin upcomer velocity-arrow side view using the existing
ParaView branch-arrow renderer and staged reconstructed render input. The new
view is `side_x`: a slice normal to `x`, with camera normal to `x`, so it is
orthogonal to the original front view that looked normal to `z`.

## Outputs

| Format | Path |
| --- | --- |
| PNG | `figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/png/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows_side_x.png` |
| SVG | `figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows_side_x.svg` |
| PDF | `figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/pdf/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows_side_x.pdf` |
| Status | `work_products/2026-07/2026-07-21/2026-07-21_thesis_upcomer_orthogonal_arrow_render/salt4_upcomer_side_x_status.json` |

## Scheduler

- First attempt: job `3308604`, failed before image output because the new
  `plane_span` helper used an invalid `max` call.
- Corrected attempt: job `3308608`, `COMPLETED 0:0` on `NuclearEnergy-dev`.
- ParaView still emitted the known post-write segmentation-fault message in the
  raw `pvbatch` log after writing outputs. The scheduler wrapper followed the
  existing render workflow: final success is based on status JSON and required
  PNG/SVG/PDF artifacts, all of which exist and report rendered.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, Fluid source,
external repository, fit, tuning, model selection, closure admission, final
score, or runtime-leakage policy changed. This is a diagnostic visualization
asset only.
