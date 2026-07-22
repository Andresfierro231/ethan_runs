---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - operational_notes/07-26/20/2026-07-20_THESIS_RECIRCULATION_IMAGE_CANDIDATES.md
  - operational_notes/07-26/21/2026-07-21_THESIS_UPCOMER_RECIRCULATION_VISUAL_EVIDENCE_INSERTION.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_upcomer_orthogonal_arrow_render/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_orthogonal_arrow_views/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_side_neg_x_arrow_view/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_y_velocity_arrow_views/README.md
tags: [thesis-section, current-section, figures, diagrams, figure-plan, segment-atlas, upcomer, sam]
related:
  - TODO-THESIS-FIGURES-DIAGRAMS
  - TODO-THESIS-ENRICHMENT-RESEARCH-AVENUES
task: AGENT-524
date: 2026-07-17
role: Coordinator/Figures/Writer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Thesis Figures And Diagrams Plan

## Purpose

This is the figure brief for the post-AGENT-516 thesis diagram lane. The goal is
to turn the current thesis text into visual, mentor-facing and thesis-ready
figures without changing scientific admission state. The figures should explain
the model architecture, evidence discipline, and unresolved blockers more
clearly than tables alone.

The first figure agent should produce editable source files plus exported
publication-friendly variants. SVG is preferred for line diagrams. Keep every
figure tied to a source section and claim ID so the visuals do not drift into
unsupported claims.

## Figure Set

| ID | Figure | Source section | Main thesis claims | Required message |
| --- | --- | --- | --- | --- |
| F-01 | `fluid+walls` loop segment atlas | `09_fluid_walls_segment_atlas.md` | CL-03, CL-11, CL-16, CL-17 | The 1D model is a loop of named fluid+wall regions with local pressure, heat, recirculation, uncertainty, and admission roles. |
| F-02 | Segment-local thermal/pressure ledger inset | `02_model_form_fluid_walls.md`, `09_fluid_walls_segment_atlas.md` | CL-02, CL-03, CL-17, CL-18 | Each segment carries separate pressure and thermal lanes; heat loss is not one cleanup multiplier. |
| F-03 | Upcomer hybrid schematic | `04_upcomer_recirculation_modeling.md`, `09_fluid_walls_segment_atlas.md` | CL-14, CL-15 | The upcomer needs a throughflow path plus recirculation/exchange lane, not ordinary single-stream pipe coefficients. |
| F-03A | Salt2/Salt4 upcomer velocity-arrow evidence pair | `04_upcomer_recirculation_modeling.md`, `18_ch6_csem_closure_admission_uncertainty.md`, `19_ch7_csem_pressure_thermal_predictive_results.md` | CL-14, CL-15 | Existing OpenFOAM velocity visuals show why the upcomer should not be reduced to an ordinary single-stream or 2D-axisymmetric closure basis in recirculating regimes. |
| F-04 | Junction-aware vs segment-only comparison | `05_junction_aware_ledgers.md`, `08_thesis_claim_ledger.md` | CL-11, CL-12, CL-13 | Junction/stub heat ownership shifts residual interpretation; pressure corner K remains diagnostic. |
| F-05 | M0-M6 model-form ladder | `06_intermediate_model_forms_and_endpoint_strategy.md` | CL-04, CL-05, CL-23, CL-24 | The thesis can compare a ladder from setup-only baseline to frozen final predictive candidate while preserving runtime and split legality. |
| F-06 | SAM-facing closure/admission flowchart | `11_sam_facing_interpretation.md` | CL-02, CL-16, CL-20, CL-25 | The SAM-facing outcome is a vetted closure/admission workflow, not SAM validation. |

## Initial SVG Set

The first static SVG set now exists at `reports/thesis_dossier/figures/`.

| ID | Current SVG |
| --- | --- |
| F-01 | `reports/thesis_dossier/figures/svg/F01_fluid_walls_loop_segment_atlas.svg` |
| F-02 | `reports/thesis_dossier/figures/svg/F02_segment_local_ledger_inset.svg` |
| F-03 | `reports/thesis_dossier/figures/svg/F03_upcomer_hybrid_schematic.svg` |
| F-03A | External existing assets; use SVG first and PDF fallback if the thesis toolchain needs it. |
| F-04 | `reports/thesis_dossier/figures/svg/F04_junction_aware_vs_segment_only.svg` |
| F-05 | `reports/thesis_dossier/figures/svg/F05_model_form_ladder.svg` |
| F-06 | `reports/thesis_dossier/figures/svg/F06_sam_facing_flowchart.svg` |

These are hand-authored conceptual diagrams. They are editable SVG source files
and current thesis-facing exports. Later figure work can polish styling or add
PDF/PNG exports without changing the underlying claim boundaries.

## Visual Requirements

### F-01: `fluid+walls` Loop Segment Atlas

Show the physical loop as named regions:

- heater/lower leg;
- lower upcomer inlet;
- bare-quartz test section;
- upper upcomer outlet;
- cooler/HX upper branch;
- downcomer/right leg;
- junction/stub/connector regions;
- corners/bends/local pressure features;
- TP/TW sensor projection layer as outputs only.

Use a small legend for status:

- admitted geometry;
- partial wall/material stack;
- diagnostic pressure coefficient;
- target-only thermal evidence;
- recirculation/hybrid flag;
- blocked/future lane.

Do not show Salt2 +/-5Q or `val_salt2` realized heat/pressure values as runtime
inputs. If values appear, label them as target or external-test evidence.

### F-02: Segment-Local Ledger Inset

Show one generic segment with two side-by-side ledgers:

```text
Pressure: distributed loss -> reset/development -> local K/branch feature -> residual
Thermal: heater/cooler -> internal convection -> wall/layer -> external convection/radiation -> residual
```

The visual should make the distinction between a model slot and an admitted
coefficient explicit. A slot may exist while the coefficient remains diagnostic
or blocked.

### F-03: Upcomer Hybrid Schematic

Show:

- net loop throughflow path;
- recirculation cell or exchange path;
- test-section span inside the upcomer;
- flag showing ordinary `Nu`, `f_D`, and `K` labels are blocked for
  recirculation-dominated rows;
- optional onset/anchor lane for future work.

Avoid making the recirculation path look like a fitted final coefficient. It is
a model-form requirement and blocker-aware schematic.

### F-03A: Salt2/Salt4 Upcomer Velocity-Arrow Evidence Pair

Use existing OpenFOAM-rendered visuals as the real CFD companion to F-03.
Preferred source paths are:

```text
figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows.svg
figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg
figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows_side_x.svg
figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_x.svg
figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_neg_x.svg
figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_y.svg
figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_z.svg
```

PDF fallbacks are available under the sibling `pdf/` directories with the same
base filenames. The orthogonal Salt4 file is a side view normal to `x`; use it
when the thesis needs a camera direction normal to the original front view. The
Salt2 validation/external orthogonal set provides page-aligned `side_x`,
`side_neg_x`, `side_y`, and `side_z` companions to the liked front-view render.
The `side_neg_x` render is the opposite camera side of `side_x`; both x-normal
views are slender projections, while `side_y` is the clearest horizontal
loop-head view. If a nominal Salt2 Jin companion is required, use the registry
velocity-profile SVG, not the external Salt2 arrow render:

```text
registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/plots/velocity_profiles/svg/registry_velocity_final.svg
```

If the thesis needs the vertical throughflow component instead of magnitude,
use the separate `U_y` arrow set:

```text
figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_y_component_arrows_side_x.svg
figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_y_component_arrows_side_neg_x.svg
figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_y_component_arrows_side_y.svg
figures/figures_rendered/paraview_velocity_y_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_y_component_arrows_side_z.svg
```

These y-component renders use arrows oriented by `U_y*jHat`, glyph length from
`abs(U_y)`, and signed color from `U_y`; they are for qualitative vertical-flow
diagnostics only. The `side_z` and x-normal views read most directly as
up/down-flow images; the `side_y` view looks along the y direction, so
y-directed glyphs appear mostly as circular arrow ends.

Caption the figure as diagnostic recirculation evidence. It may justify
abandoning ordinary single-stream and 2D-axisymmetric upcomer closure as the
working basis for this regime, but it must not be captioned as an admitted
ordinary upcomer `Nu`, `f_D`, component `K`, or exchange-cell coefficient.

### F-04: Junction-Aware vs Segment-Only Comparison

Use a split-panel figure:

- left: segment-only model with losses absorbed into large branches;
- right: junction-aware model with separate ordinary pipe, junction/stub,
  corner, connector, and residual ownership lanes.

Include the external-test evidence label:

```text
val_salt2 junction/stub heat target: about 40.93 W across four buckets
```

Also include a pressure caveat label:

```text
corner K: diagnostic only; 0 fit-admitted rows
```

### F-05: M0-M6 Model-Form Ladder

Show a horizontal or vertical ladder:

| Form | Short label |
| --- | --- |
| M0 | setup-only baseline |
| M1 | CFD thermal-boundary replay diagnostic |
| M2 | admitted heater+cooler boundary model |
| M3 | segment-only `fluid+walls` |
| M4 | junction-aware `fluid+walls` |
| M5 | hybrid upcomer |
| M6 | frozen final predictive candidate |

Each rung should show:

- allowed runtime input status;
- predictive/diagnostic/blocked/future label;
- increasing model structure;
- split discipline: train/support/holdout/external.

M6 must be shown as the desired endpoint or pending frozen candidate, not as a
completed final result unless a later scorecard lands.

### F-06: SAM-Facing Closure/Admission Flowchart

Show the flow:

```text
CFD evidence
  -> 3D-to-1D reduction
  -> branchwise pressure ledger / heat ledger / recirculation flags
  -> admission + uncertainty + split labels
  -> SAM-facing model construction guidance
  -> future SAM validation, not claimed here
```

The final box should say "future SAM validation" or "not yet validated in SAM"
so the boundary is visible.

## Deliverable Contract For The Figure Agent

The future figure agent should produce:

- a figure package README;
- editable sources for each diagram, preferably SVG source or a script that
  writes SVG;
- exported `svg` for all diagrams;
- exported `pdf` or `png` variants if thesis/presentation tooling needs them;
- caption text for each figure;
- a figure-to-claim crosswalk table;
- a source manifest listing the thesis sections and work-product files used.

Recommended package locations:

```text
reports/thesis_dossier/figures/
work_products/2026-07/2026-07-17/2026-07-17_thesis_figures_diagrams/
```

Use `reports/thesis_dossier/figures/` for durable thesis-facing outputs if a
new folder is acceptable at implementation time. Use `work_products/` for
generated intermediates, proofs, and scripts if the figure build is more than a
hand-authored SVG set.

## Style Guidance

- Prefer clean line diagrams over dense data plots for this lane.
- Use consistent colors for evidence status:
  - admitted: green;
  - partial/caveated: blue or gray;
  - diagnostic: amber;
  - blocked/future: red or muted gray.
- Use short labels and put caveats in captions or small callouts.
- Keep split roles visible where a figure could be mistaken as training
  evidence.
- Do not use decorative gradients or visual effects that obscure technical
  meaning.

## Acceptance Checklist

| Check | Requirement |
| --- | --- |
| Source traceability | Every figure cites its source section and claim IDs. |
| No overclaim | Diagnostic pressure K, internal Nu, and upcomer coefficients are visually labeled diagnostic/blocked where applicable. |
| Runtime legality | Figures do not imply realized CFD outputs are predictive runtime inputs. |
| Split legality | Holdout and external rows are not shown as fit/tune evidence. |
| Reproducibility | Editable source files are checked in or generated by a committed script. |
| Thesis usability | Each figure has a caption and suggested chapter placement. |

## Suggested Chapter Placement

| Chapter area | Figures |
| --- | --- |
| Methodology / 3D-to-1D reduction | F-01, F-02 |
| Junction-aware ledgers | F-04 |
| Upcomer recirculation | F-03, F-03A |
| Forward predictive model | F-05 |
| SAM-facing interpretation / conclusion | F-06 |

## 2026-07-22 Readiness Refresh

Current readiness packet:
`work_products/2026-07/2026-07-22/2026-07-22_thesis_figures_diagrams/`.

F-01 through F-06 are ready for claim-controlled thesis use as conceptual SVGs.
F-03A/F-03B remain diagnostic CFD visual candidates only. F-07/F-08 are future
status/uncertainty panel targets and should wait for their source packets rather
than being drawn from memory.

Guardrails for the next figure pass:

- Keep `M6` labeled as pending until a frozen runtime-legal candidate exists.
- Keep formal GCI blocked unless a true same-label mesh family is admitted.
- Keep upcomer ordinary `Nu`, `f_D`, `K`, and exchange coefficients blocked for
  current recirculating rows.
- Do not use realized CFD `wallHeatFlux`, CFD `mdot`, imposed cooler duty, or
  validation temperatures as predictive runtime inputs.
- Do not edit or duplicate the active blocked-scorecard panel package without a
  separate row.
