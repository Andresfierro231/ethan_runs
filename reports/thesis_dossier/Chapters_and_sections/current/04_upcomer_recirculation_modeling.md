---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_upcomer_recirculation_modeling_section.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-14_upcomer_recirculation_internal_nu_story.md
  - reference/geometry_reference.md
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/upcomer_admission_decision.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/recirculation_feature_scorecard.csv
  - operational_notes/07-26/20/2026-07-20_THESIS_RECIRCULATION_IMAGE_CANDIDATES.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
  - figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows.svg
  - figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg
  - registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/plots/velocity_profiles/svg/registry_velocity_final.svg
tags: [thesis-section, current-section, upcomer, recirculation, hybrid-model]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
task: AGENT-502
date: 2026-07-17
role: Writer
type: thesis-section
status: current-draft
supersedes:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_upcomer_recirculation_modeling_section.md
superseded_by:
---
# Upcomer Recirculation Modeling

## Geometry

The upcomer is not a single anonymous vertical pipe in the current model. The
loop path is:

```text
heater (lower_leg)
  -> upcomer (left_lower_leg -> test_section_span -> left_upper_leg)
  -> cooler (upper_leg)
  -> downcomer (right_leg)
  -> heater
```

The test section is the middle upcomer span. It has a smaller bore, fused-quartz
wall, no mineral insulation, and a distinct heat-source/loss role. It should not
be folded into a generic vertical-pipe closure.

## Recirculation Evidence

Current upcomer evidence contains material reverse flow in repaired PM5 rows.
The reported maximum reverse area fraction is `0.7901396438`, the maximum
reverse mass fraction is `0.5000672828`, and the maximum Richardson number is
`108.7458056`. These values indicate a section-effective recirculating regime,
not a small perturbation to ordinary one-dimensional throughflow.

The branch-specific ordinary-pipe scorecard therefore excludes the upcomer from
ordinary aggregate fits and assigns it to a hybrid-model lane.

## Visual Evidence Placement

The thesis should place an OpenFOAM upcomer velocity-arrow visual immediately
after the reverse-flow metrics. Use the Salt4 Jin upcomer velocity-arrow SVG as
the preferred mainline training-family example:

```text
figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows.svg
```

Pair it, where space allows, with the Salt2 validation/external upcomer
velocity-arrow SVG:

```text
figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg
```

If the writer needs a nominal Salt2 Jin companion rather than the external
Salt2 visual, the currently documented SVG fallback is the Salt2 Jin registry
velocity-profile plot:

```text
registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/plots/velocity_profiles/svg/registry_velocity_final.svg
```

This visual pair is evidence for model-form selection. It supports the thesis
claim that a single-stream upcomer closure, and by extension a 2D-axisymmetric
upcomer reduction used as if it were an ordinary one-stream closure basis, is
not adequate for the recirculating upcomer regime. It does not admit an
ordinary upcomer `Nu`, `f_D`, component `K`, or exchange-cell coefficient.

## Interpretation

The paper-safe interpretation is that the upcomer requires a recirculation-aware
model form. Current rows should not be used to fit ordinary single-stream
`Nu`, `f_D`, or component `K` values. Those labels would imply ordinary pipe
throughflow, while the evidence shows strong reverse-flow and mixed-convection
structure.

The defensible next model form is a throughflow-pipe plus recirculation-cell
model. One lane carries the net loop throughflow. A separate named lane carries
section-effective exchange, mixing, or penalty terms associated with the
recirculating cell.

## Paper-Safe Claims

- The upcomer path includes `left_lower_leg`, `test_section_span`, and
  `left_upper_leg`.
- The test section is the middle upcomer span and needs its own source/loss
  treatment.
- Current CFD-derived upcomer evidence shows material recirculation.
- Salt4 Jin and Salt2 validation/external velocity-arrow visuals can be used as
  diagnostic images of the recirculating regime; nominal Salt2 Jin velocity
  profiles can be used only with that separate provenance label.
- Current recirculating upcomer rows are diagnostic evidence for model-form
  selection, not admitted ordinary-pipe coefficient fits.
- A throughflow-pipe plus recirculation-cell model is the defensible next
  model form, but it remains diagnostic until onset anchors and split-safe
  scoring admit a frozen candidate.

## Unresolved Needs

- low-recirculation and transition anchors for onset calibration;
- same-window pressure, thermal, and uncertainty fields for the hybrid lane;
- mesh/time uncertainty before coarse-only recirculation features become
  predictive closures;
- coupled scorecards that show the hybrid lane improves prediction without
  using held-out row outputs at runtime.
