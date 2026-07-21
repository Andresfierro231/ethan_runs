---
provenance:
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_enrichment_writing_pass/README.md
  - ../papers/UTexas_Research/3d_analysis/sections/01_introduction_and_claim.tex
tags: [thesis-section, current-section, csem, motivation, contribution, cfd-to-1d]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md
  - reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
task: TODO-THESIS-CH1-CSEM-MOTIVATION-DRAFT
date: 2026-07-21
role: Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# CSEM Motivation And Contribution

## Purpose

This section is chapter-ready introduction prose for the CSEM thesis package.
It establishes the motivation, contribution, and claim boundary before the CFD
evidence and 1D model-form chapters. It uses only existing dossier and paper
evidence and does not edit the external dissertation tree.

## Motivation

Natural-circulation molten-salt loops are attractive reduced-scale platforms
for studying coupled hydraulic and thermal behavior in advanced reactor heat
transport systems. Their operating state is not controlled by a prescribed pump
curve. Instead, flow emerges from the balance between buoyancy drive, hydraulic
resistance, heat addition, heat removal, passive boundary losses, and local
mixing. A reduced model that predicts this behavior must therefore represent
pressure and heat ownership with enough fidelity that one error source is not
silently absorbed into another.

The TAMU molten-salt loop motivates this problem directly. The target outputs
are loop mass flow, branch and sensor temperatures, branchwise heat addition or
loss, and pressure-loss attribution. A single tuned multiplier can improve one
quantity while degrading another, especially when recirculation, junction heat
loss, test-section heat balance, property choice, or wall-boundary physics are
important. The thesis therefore treats model construction as an evidence-gated
process rather than a search for one best correction factor.

## CFD As The Present Reference

Ethan OpenFOAM CFD is the current high-fidelity reference for this thesis. The
CFD cases provide spatially resolved pressure, temperature, velocity, wall, and
heat-transfer evidence that can be reduced into one-dimensional observations.
Those observations are used to identify model-form needs, diagnose missing
physics, test candidate closures, and define score targets.

This is not an experimental-validation claim. Claim CL-01 in the thesis claim
ledger states the boundary explicitly: CFD is the present comparison reference,
not an independent experiment. Any future experimental or SAM validation would
require a separate model, frozen inputs, score tables, and corresponding
evidence package.

## Contribution

The primary contribution is a provenance-controlled CFD-to-1D closure workflow
for the TAMU molten-salt natural-circulation loop. Claim CL-02 defines this as
a branchwise closure and admission framework rather than a single tuned global
coefficient.

The workflow has three linked products:

- a CFD evidence ledger that records source paths, time windows, split roles,
  extraction status, and uncertainty labels;
- a steady `fluid+walls` one-dimensional model form with explicit pressure,
  heat, source/sink, wall, recirculation, and admission slots by segment;
- a closure-admission process that separates method evidence, diagnostic CFD
  reductions, admitted setup-facing model terms, holdout scoring, external
  scoring, and blocked claims.

This structure is the thesis value even where a candidate model fails. For
example, current pressure evidence can justify a section-effective or
diagnostic residual lane without admitting an ordinary component `K`. Current
wall/test-section evidence can narrow the thermal blocker while still rejecting
runtime-leaking or temperature-shape-worsening candidates. Negative results are
kept as evidence because they prevent later writers from hiding failed physics
inside an apparently successful scalar correction.

## Enriched Contribution Framing

The thesis should present the admission workflow itself as a scientific
contribution. The current `ethan_runs` evidence base shows that reduced-model
progress is not only a matter of finding a coefficient with a smaller residual.
Several useful analyses end with non-admission: pressure-corner rows remain
section-effective diagnostics, wall/test-section candidates narrow the
temperature-shape blocker, and upcomer exchange evidence identifies missing
recirculation variables without admitting an exchange cell.

That pattern is central to the motivation. A CSEM-facing or SAM-facing model
needs a way to decide when a local pressure or heat term is allowed to become a
runtime input. The thesis contribution is therefore the combination of model
form and gatekeeping: the `fluid+walls` architecture exposes the needed slots,
and the admission ledger decides whether each slot is admitted, diagnostic,
score-only, or blocked.

## Thesis Through-Line

The thesis should be read as a progression from evidence to admissible reduced
modeling:

1. The loop physics require local pressure and heat ownership.
2. CFD provides the present high-fidelity evidence base, with provenance and
   trust limits.
3. The 1D target is a steady `fluid+walls` model whose segment fields mirror
   the observed pressure, heat, wall, and recirculation roles.
4. Literature supplies source envelopes and candidate model forms, but it does
   not automatically admit a TAMU closure.
5. The admission ledger decides which terms are method-ready, diagnostic,
   partially admitted, score-only, or blocked.
6. The final predictive path must use setup-known runtime inputs only.

This framing keeps the thesis defensible if final predictive scoring remains
blocked by wall/test-section, pressure, F6, or upcomer evidence gaps.

## Draft Introduction Paragraph

This thesis develops a reduced-order modeling workflow for the TAMU
molten-salt natural-circulation loop using Ethan OpenFOAM CFD as the current
high-fidelity reference. The objective is not to tune a single global loss or
heat-transfer multiplier. The objective is to construct a one-dimensional
`fluid+walls` model in which each pressure, heat, wall, source/sink,
recirculation, property, and uncertainty term carries provenance and admission
status. CFD reductions are used to motivate and score this model, but they are
not treated as experimental validation. The resulting contribution is a
branchwise CFD-to-1D closure ledger that distinguishes setup-facing predictive
inputs from diagnostic replay evidence and from claims that remain blocked
until additional model or uncertainty work is completed.
