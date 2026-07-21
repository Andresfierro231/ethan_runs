---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_modeling_approach_section.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_current_context.md
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md
  - operational_notes/maps/literature-synthesis-and-gates.md
  - operational_notes/maps/forward-predictive-model.md
tags: [thesis-section, current-section, modeling-approach, cfd-to-1d, methodology]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
task: AGENT-502
date: 2026-07-17
role: Writer
type: thesis-section
status: current-draft
supersedes:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_modeling_approach_section.md
superseded_by:
---
# Modeling Approach

## Purpose

This thesis develops a CFD-to-1D modeling workflow for the TAMU molten-salt
natural-circulation loop. The goal is not to extract one global closure
coefficient from CFD. The goal is to build a lower-order model whose assumptions
are explicit enough that pressure, heat-transfer, boundary-condition,
property-mode, mesh, and admission uncertainties do not hide inside one fitted
multiplier.

Ethan OpenFOAM CFD is treated as the present high-fidelity reference. It is used
to diagnose model form, calibrate admitted closure terms, and score predictive
behavior under a documented split policy. It is not experimental validation.

## Workflow

The modeling approach has four stages.

1. Build a provenance-controlled evidence ledger from CFD cases.
2. Reduce CFD fields into 1D pressure, heat, temperature, and validity
   observations.
3. Admit or reject closure terms using literature, physics, mesh, steady-state,
   recirculation, and split-policy gates.
4. Assemble a setup-only forward 1D model and score it on rows not used for
   fitting or model selection.

This workflow keeps explanation, calibration, and prediction separate. A CFD
replay can explain which physical term controls an error, but a final
predictive model must use only setup-known runtime inputs.

## Evidence Ledger

Every thesis claim should trace to a source path, time window, extraction
script, generated package, and admission status. Case rows are organized by
their role in the evidence hierarchy:

- mainline admitted Salt/Jin rows provide primary thesis evidence;
- Salt-Q perturbation rows support sensitivity, trend checks, and holdout
  scoring when row-specific admission allows it;
- `val_salt2` is an external-test row after matching heat-loss and admission
  evidence;
- Kirst rows remain historical unless a later dated note explicitly re-admits
  them;
- replay modes are diagnostic unless they obey the final runtime-input
  contract.

Blockers are preserved as part of the result. If a row cannot support a claim
because of recirculation, wall/test-section uncertainty, missing onset anchors,
mesh limitations, pressure-plane ambiguity, or runtime leakage, the limitation
is carried forward instead of being absorbed into a fitted coefficient.

## 3D-To-1D Reduction

The 3D-to-1D reduction is a physical mapping, not a simple averaging procedure.
Pressure observations depend on pressure basis, elevation, density, dynamic
pressure, and tap or plane placement. Heat observations depend on patch role,
sign convention, enthalpy change, wall material, external boundary condition,
and radiation treatment. Sensor-temperature observations depend on coordinate
mapping and whether the 1D model path actually reaches the sensor location.

The pressure balance can be written compactly as

$$
\Delta p_{drive}(\dot{m},T)
\approx
\Delta p_{loss}(\dot{m},T,\mathrm{geometry},\mathrm{closures}),
$$

but the compact form is only a root-solve statement. In the ledger, buoyancy is
integrated over the loop:

$$
\Delta p_{drive}
= \oint \rho(T(s),p(s),x) g\,dz(s),
$$

and loss terms are accumulated by segment:

$$
\Delta p_{loss}
= \sum_i
\left[
f_i(Re_i,Pr_i,Ri_i,\mathrm{geometry}_i,\mathrm{reset}_i)\frac{L_i}{D_i}
+ K_i(\mathrm{geometry}_i,\mathrm{development}_i,\mathrm{regime}_i)
\right]\frac{1}{2}\rho_i V_i^2.
$$

The thermal ledger is similarly separated:

$$
\dot{m}\bar{c}_{p,i}(T_{out,i}-T_{in,i})
= Q_{heater,i}
- Q_{cooler,i}
- Q_{passive,i}
+ Q_{test,i}
+ Q_{junction,i}
+ Q_{residual,i}.
$$

The residual is an accounting result. It is not automatically internal
convection, heater inefficiency, cooler error, wall loss, or radiation. It is
assigned only after the corresponding source/sink lane passes its admission
gate.

## Literature-Gated Closure

The literature review is used as a gate for model forms. Each candidate closure
is documented by source family, equation form, required inputs, validity
envelope, TAMU overlap, and use status. Fully developed pipe correlations are
kept as references unless the local segment satisfies the assumptions. Fitting
or cluster losses are labeled according to what the pressure planes actually
isolate. Internal heat-transfer coefficients are not allowed to absorb passive
loss, cooler duty, heater residual, radiation, wall/test-section uncertainty,
or recirculation effects.

This is the central methodological contribution: closure terms are admitted
branchwise and sourcewise rather than globally.

## Predictive Assembly

The final 1D model couples the hydraulic and thermal ledgers. Hydraulic
prediction changes the thermal problem because mass flow controls residence time
and advective heat capacity. Thermal prediction changes the hydraulic problem
because temperature controls density, viscosity, buoyancy, and Reynolds number.

The model is assembled from setup-known inputs and admitted closure terms:

- geometry and segment map;
- property lane;
- heater setup model;
- cooler/HX setup model;
- passive wall and external-boundary model;
- explicit test-section source/loss model;
- pressure-loss model;
- sensor map;
- uncertainty and admission labels.

Any mode that consumes CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD
cooler duty, validation temperatures, or held-out pressure/heat targets at
runtime is diagnostic. Diagnostic modes are important for discovering missing
physics, but they are not final prediction.
