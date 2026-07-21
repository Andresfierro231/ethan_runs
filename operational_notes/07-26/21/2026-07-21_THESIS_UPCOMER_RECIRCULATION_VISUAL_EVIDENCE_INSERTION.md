---
provenance:
  - .agent/BOARD.md
  - operational_notes/07-26/20/2026-07-20_THESIS_RECIRCULATION_IMAGE_CANDIDATES.md
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
  - reports/thesis_dossier/figures/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/caption_bank.md
  - figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows.svg
  - figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg
  - registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/plots/velocity_profiles/svg/registry_velocity_final.svg
tags: [thesis-dossier, upcomer, recirculation, figures, diagnostic-evidence]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
task: TODO-THESIS-UPCOMER-RECIRCULATION-VISUAL-EVIDENCE-INSERTION-2026-07-21
date: 2026-07-21
role: Writer/Reviewer/Figures
type: operational_note
status: complete
supersedes: []
superseded_by:
---
# Thesis Upcomer Recirculation Visual Evidence Insertion

## Why This Exists

The thesis now has enough diagnostic evidence to include a real CFD visual next
to the F-03 upcomer hybrid schematic. The useful claim is narrow: current
upcomer evidence shows material recirculation, so ordinary single-stream
closure and a 2D-axisymmetric upcomer reduction used as an ordinary one-stream
closure basis are not adequate for this regime.

## Open First

1. `reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md`
2. `reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md`
3. `reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md`
4. `reports/thesis_dossier/figures/README.md`
5. `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/README.md`
6. `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md`

## Figure Sources

| Role | Source path | Use |
| --- | --- | --- |
| Salt4 mainline visual | `figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows.svg` | Preferred mainline training-family upcomer velocity-arrow visual. |
| Salt2 external visual | `figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg` | Salt2 validation/external companion; label as external/test evidence. |
| Salt2 Jin fallback | `registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/plots/velocity_profiles/svg/registry_velocity_final.svg` | Nominal Salt2 Jin velocity-profile fallback if the thesis needs nominal Salt2 provenance rather than the external Salt2 arrow render. |

SVG should be used first. PDF fallbacks exist for the Salt4 and Salt2 external
arrow renders under sibling `pdf/` directories with the same base filenames.

## Target Placement

Place F-03A in the upcomer recirculation/model-form discussion, immediately
after the reverse area fraction, reverse mass fraction, and Richardson-number
paragraph. It can also support Chapter 6 admission/uncertainty and Chapter 7
negative/diagnostic results, paired with the ordinary-closure exclusion table
and S9 exchange-QOI contract.

## Caption Guardrail

Allowed caption meaning:

```text
Salt2/Salt4 upcomer velocity evidence illustrates material recirculation and
supports the throughflow-plus-recirculation model-form requirement. Ordinary
single-stream upcomer Nu, f_D, K, and exchange-cell coefficients remain
unadmitted.
```

Forbidden caption meanings:

- admitted ordinary upcomer `Nu`, `f_D`, or component `K`;
- admitted exchange-cell coefficient;
- final predictive score or SAM validation;
- use of external Salt2 as training/tuning evidence;
- use of CFD `mdot`, realized `wallHeatFlux`, imposed cooler duty, realized
  test-section heat, or validation temperatures as predictive runtime inputs.

## Next Task Sequence

1. A later figure-production row may copy/export the selected F-03A assets into
   the thesis build tree if the external dissertation toolchain requires local
   figure assets.
2. A writing row can insert the F-03A caption into the external thesis draft
   with the split-role labels preserved.
3. S13 remains the required scientific row for production exchange QOIs and
   same-window UQ; this visual insertion does not unblock exchange-cell
   admission.
