---
provenance:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_current_context.md
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/literature-synthesis-and-gates.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
tags: [thesis-section, modeling-approach, cfd-to-1d, closure-ledger, methodology]
related:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_model_form_section.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_split_policy_section.md
  - reports/thesis_dossier/Outline.md
task: AGENT-497
date: 2026-07-17
role: Writer
type: thesis-section
status: draft
supersedes: []
superseded_by:
---
# Draft Thesis Section: Modeling Approach

## Section Role

This section is a comprehensive methodology narrative. It should become the
bridge between the literature review, the CFD case/admission chapter, the
hydraulic and thermal closure chapters, and the final predictive 1D model
chapter. The central idea is that the thesis does not extract one global closure
coefficient from CFD. It builds a controlled pathway from high-fidelity CFD
evidence to a lower-order 1D model, while preserving the conditions under which
each closure term is valid.

## Thesis-Level Objective

The objective is to develop a defensible 1D model for the TAMU molten-salt
natural-circulation loop. The model should eventually predict loop mass flow and
temperatures from physical setup inputs: geometry, material state, heater
settings, cooler/HX settings, external boundary conditions, and admitted closure
parameters. Ethan OpenFOAM CFD is used as the current high-fidelity reference,
but it is not experimental validation. The thesis therefore treats CFD as
calibration and diagnostic evidence, not as proof that the model is correct in
the real facility.

The modeling approach has four linked stages:

1. Establish a trustworthy evidence ledger from CFD.
2. Reduce CFD fields into 1D pressure, heat, temperature, and validity
   observations.
3. Admit or reject closure terms using literature, physics, mesh, steady-state,
   and split-policy gates.
4. Assemble a setup-only forward 1D model and score it on rows not used for
   fitting or model selection.

## Stage 1: Evidence Ledger

The first stage is documentation and admission control. Each case or row must
carry provenance before it contributes to a thesis claim. Required provenance
includes the source case path, continuation status, time window, extraction
script, generated package, and admission status. This prevents the thesis from
mixing current mainline continuations with superseded warmups or historical
variants.

The current evidence hierarchy is:

- mainline admitted Salt/Jin rows for primary thesis evidence;
- Salt-Q perturbation rows for sensitivity, support, and holdout/testing roles
  after row-specific admission;
- `val_salt2` as external-test evidence after matching heat-loss and admission
  package;
- Kirst rows as historical context unless later explicitly re-admitted;
- diagnostic replay modes as model-form evidence, not final predictive claims.

This stage also preserves blockers. If a result cannot support a claim because
of recirculation, wall/test-section uncertainty, missing onset anchors, mesh
limits, pressure-plane ambiguity, or runtime leakage, the limitation is part of
the scientific result.

## Stage 2: 3D-to-1D Reduction

The second stage maps CFD fields onto a 1D representation. This reduction is not
a simple averaging operation. Each quantity is tied to a physical and numerical
meaning:

- pressure depends on basis, elevation, density, dynamic pressure, and tap or
  plane placement;
- heat transfer depends on patch role, sign convention, wall material, external
  boundary condition, and enthalpy change;
- sensor temperature depends on sensor coordinate and whether the 1D path
  location is known;
- apparent coefficients depend on whether the sampled region is single-stream,
  isolated, and mesh/admission compatible.

The pressure reduction starts from the loop balance:

$$
\Delta p_{drive}(\dot{m},T)
\approx
\Delta p_{loss}(\dot{m},T,geometry,closures).
$$

The compact equation is only a root-solve statement. The thesis should not imply
that either side is one global function. In the actual ledger, buoyancy is
integrated over the loop density/elevation field:

$$
\Delta p_{drive}
= \oint \rho(T(s),p(s),x) g\,dz(s),
$$

and losses are accumulated by segment:

$$
\Delta p_{loss}
= \sum_i
\left[
f_i(Re_i,Pr_i,Ri_i,geometry_i,reset_i)\frac{L_i}{D_i}
+ K_i(geometry_i,development_i,regime_i)
\right]
\frac{1}{2}\rho_i V_i^2.
$$

The thermal reduction follows a parallel ledger:

$$
\dot{m}\bar{c}_{p,i}(T_{out,i}-T_{in,i})
= Q_{heater,i}
- Q_{cooler,i}
- Q_{passive,i}
+ Q_{test,i}
+ Q_{junction,i}
+ Q_{residual,i}.
$$

The residual is not assigned to internal convection by default. It remains a
residual until the heater, cooler, passive wall, radiation, material stack,
test-section, and junction lanes are separated well enough to justify a closure
claim.

## Stage 3: Literature-Gated Closure

The literature review is used as a gate, not as decoration. For each candidate
closure, the thesis records:

- source family and author/title provenance;
- equation form and required inputs;
- validity envelope in Reynolds, Prandtl, Richardson, Rayleigh, Graetz,
  geometry, orientation, and heating/cooling regime;
- overlap with TAMU branch conditions;
- data required to fit or score the term;
- thesis use status: reference, active candidate, diagnostic, rejected, or
  future work.

This approach changes how closure terms are interpreted. A fully developed
friction factor or Nusselt number may be a useful reference, but it is not
automatically valid in short, developing, strongly heated, recirculating, or
close-coupled regions. A component `K` may be appropriate for an isolated bend,
but pressure taps spanning a bend, reducer, tee, and local recirculation region
produce a cluster or branch-apparent quantity. A CFD-derived `Nu` may diagnose
thermal structure, but it should not absorb passive heat loss, cooler duty,
radiation, or wall/test-section errors.

## Stage 4: Predictive Assembly

The final 1D model is assembled only from admitted terms and setup-only inputs.
The model predicts `mdot` and temperatures by coupling the pressure and thermal
ledgers. Hydraulic prediction changes the heat problem because mass flow sets
residence time and advective heat capacity. Thermal prediction changes the
hydraulic problem because temperature sets density, viscosity, buoyancy, and
local Reynolds number. The final model must therefore solve the coupled problem
rather than fit thermal and hydraulic residuals independently.

The current model target is steady `fluid+walls`. The model includes:

- segment-local pressure losses;
- branchwise buoyancy drive;
- heater setup model;
- cooler/HX setup model;
- passive wall and external-boundary model;
- explicit test-section source/loss model;
- material stack and drive-temperature convention;
- sensor prediction map;
- admission and uncertainty labels for every scored quantity.

Replay modes remain useful during assembly. For example, imposing CFD cooler
duty can show that cooler/HX heat removal is the first-order thermal lever.
However, imposed CFD duty is not a setup-only input, so that result is
diagnostic. The predictive successor must replace imposed quantities with
models whose inputs are known before the CFD result is observed.

## Current Claim Boundaries

The present evidence supports the following thesis claims:

- A branchwise closure ledger is better supported than one global fitted
  coefficient.
- The final model form should be steady `fluid+walls`, not fluid-only plus a
  fitted heat leak.
- Salt1 nominal and admitted Salt1 perturbations can now be used confidently in
  their documented roles.
- Heater and cooler/HX setup-only submodels are admitted boundary evidence.
- Recirculating upcomer rows cannot be used as ordinary single-stream
  coefficient fits.
- Final predictive scoring must separate training, support, holdout/testing,
  and external-test rows.

The present evidence does not yet support:

- a final admitted wall/test-section/passive-boundary model;
- ordinary upcomer `Nu`, `f_D`, or local `K` fits from recirculating rows;
- final promotion of F6 friction/Re correction;
- a predictive claim for modes that consume CFD `mdot`, realized `wallHeatFlux`,
  imposed CFD cooler duty, or validation temperatures at runtime.

## Draft Thesis Wording

The methodology developed in this thesis treats CFD-to-1D modeling as an
admission-controlled reduction problem. CFD fields are first converted into
pressure, heat, temperature, and validity observations with explicit provenance.
Those observations are then filtered through literature envelopes,
steady-state checks, mesh and reconstruction status, physical validity
diagnostics, and the final training/testing split. Only terms that pass the
appropriate gates are allowed to become predictive model inputs.

This structure is necessary because the TAMU loop does not behave as a set of
long, isolated, fully developed pipe sections. Heat addition, heat removal,
external losses, wall materials, fittings, short development lengths, and
recirculation all interact with the natural-circulation mass flow. A coefficient
that appears to close one balance can hide an error in another balance if its
source lane is not preserved. The thesis therefore separates hydraulic,
thermal, boundary-condition, property, mesh, steady-state, and runtime-input
uncertainties before fitting or scoring a closure.

The final deliverable is a setup-only predictive 1D model pathway. Diagnostic
CFD replay is used to identify missing physics and prioritize submodels, but the
final scorecards exclude CFD outputs from runtime inputs. This distinction lets
the thesis use CFD aggressively as evidence while preserving the difference
between explanation, calibration, and prediction.
