---
provenance:
  - figures/figures_rendered/paraview_field_families/upcomer/y_vel/
  - figures/figures_rendered/paraview_velocity_arrows/
  - work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/figures/11_upcomer_recirculation_schematic.png
  - reports/2026-06/2026-06-29/2026-06-29_ethan_upcomer_recirculation_evidence/figures/svg/upcomer_reverse_shear_fraction_profile.svg
  - reports/thesis_dossier/figures/svg/F03_upcomer_hybrid_schematic.svg
tags: [thesis, figures, recirculation, upcomer, cfd-visuals]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - TODO-THESIS-FIGURES-DIAGRAMS
task: AGENT-562
date: 2026-07-20
role: Writer/Figures/Coordinator
type: operational_note
status: complete
---
# Thesis Recirculation Image Candidates

This note records recirculation/upcomer image candidates that are likely useful
for the thesis. It does not regenerate images or change scientific admission
state.

## Best Candidate Uses

Use the rendered ParaView images when the thesis needs a real CFD visual:

- `figures/figures_rendered/paraview_field_families/upcomer/y_vel/png/`
- `figures/figures_rendered/paraview_field_families/upcomer/y_vel/svg/`
- `figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_1_jin_coarse_mesh/upcomer/`
- `figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_3_jin_coarse_mesh/upcomer/`
- `figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/`
- `figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/`

Use these for slides or as starting points for thesis figures:

- `work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/figures/11_upcomer_recirculation_schematic.png`
- `work_products/2026-07/2026-07-02/2026-07-02_master_jul_2_presentation/figures/fig6_recirculation.png`
- `work_products/2026-07/2026-07-01/2026-07-01_claude_checkpoint_presentation/fig6_recirculation.png`

Use these for quantitative recirculation/onset evidence:

- `reports/2026-06/2026-06-29/2026-06-29_ethan_upcomer_recirculation_evidence/figures/svg/upcomer_reverse_shear_fraction_profile.svg`
- `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/upcomer_backflow_vs_re.svg`
- `work_products/2026-07/2026-07-08/2026-07-08_upcomer_onset/figures/upcomer_onset_regime.svg`

Use this as the current editable thesis schematic source:

- `reports/thesis_dossier/figures/svg/F03_upcomer_hybrid_schematic.svg`

## Guardrails

- Label real CFD images as evidence/diagnostics, not as a validated final
  closure.
- Do not imply ordinary single-stream `Nu`, `f_D`, or component-`K` admission
  for recirculation-dominated upcomer rows.
- If using Salt1 Kirst or other historical images, check whether the figure is
  only illustrative. Current thesis claims should prefer admitted/current
  Salt/Jin or explicitly labeled validation/external-test evidence.
- Preserve source paths in captions or figure manifests so later thesis edits
  can trace each visual back to its package.
- For final thesis export, prefer SVG/PDF where available; use PNG only when
  the source is a rendered bitmap or a presentation image.

## Next Useful Action

When `TODO-THESIS-FIGURES-DIAGRAMS` is claimed, review these candidates against
the thesis figure plan and decide whether to reuse, redraw, or regenerate each
image. The likely pair is one real upcomer CFD field/arrow image plus the
`F03_upcomer_hybrid_schematic.svg` conceptual figure.
