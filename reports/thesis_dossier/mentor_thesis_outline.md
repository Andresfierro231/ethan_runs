---
provenance:
  - user_feedback_corrected_outline_2026-07-20
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md
tags: [thesis-dossier, mentor-facing, thesis-outline, proposed-outline, canonical]
related:
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/README.md
task: THESIS-CORRECTED-OUTLINE-2026-07-20
date: 2026-07-20
role: Writer/Reviewer
type: report
status: current-canonical-outline
supersedes:
  - AGENT-532
superseded_by:
---
# Proposed Master's Thesis Outline

## Working Title

**CFD-to-1D Model Reduction for Molten-Salt Natural-Circulation Loops: Local Closure Identification and Predictive Model Assessment**

## Central Thesis Claim

Preliminary CFD evidence from the low-Reynolds-number TAMU loop cases indicates that a single loop-wide correction factor is insufficient to represent the spatially distinct heat-transfer and pressure-loss behavior. The one-dimensional treatment therefore appears to require, at minimum, leg-specific closures; regions such as the recirculating upcomer may require a distinct model form rather than a scalar correction. A defensible model requires:

1. local reduction of the three-dimensional behavior;
2. explicit segmentwise heat and pressure balances;
3. appropriate treatment of developing flow, junctions, recirculation, wall conduction, and external heat transfer;
4. separation of calibration, diagnostic, holdout, and validation evidence; and
5. documented criteria for deciding which closures can be used predictively.

## Problem Statement And Proposed Research Questions

1. Which three-dimensional molten salt natural circulation loop CFD effects must be represented locally for the one-dimensional model to predict mass flow and temperature locations?

2. Under what conditions are conventional pipe-flow closures invalid because of developing flow, junction interactions, recirculation, or coupled wall and environmental heat transfer?

3. Which leg-specific or component-specific model formulations improve prediction of mass flow and temperature distributions relative to a model using conventional loop-wide corrections?

4. How do property uncertainty, temporal variability, mesh sensitivity, sensor mapping, and data-role assignment affect whether a fitted closure can be used predictively?

## Future Work Questions

1. How can the resulting framework inform future implementation in a systems code such as SAM?

2. What physical evidence, error bounds, and evaluation results are required before a candidate closure can be included in forward predictions?

## Contribution Boundary

### Largest Collaborative Inputs

- TAMU molten-salt natural-circulation loop geometry and experimental measurements.
- OpenFOAM CFD cases developed by Ethan Rozak.
- Existing molten-salt property models and published closure correlations.

### Proposed Thesis Contributions

- Definition of the CFD-to-1D segmentation and data-reduction methodology.
- Construction of segmentwise heat and pressure balance decompositions.
- Identification and evaluation of component-local closure candidates.
- Definition of closure-selection criteria and predictive-input restrictions that prevent outputs from the target CFD case from being used as inputs to the one-dimensional model.
- Formulation of coupled fluid-and-wall one-dimensional model forms.
- Comparison of segment-only, junction-aware, and hybrid-upcomer formulations.
- Held-out predictive assessment of mass flow, temperatures, heat balances, and pressure balances.
- Translation of the findings into recommendations for future systems-code implementation.

# 1. Introduction And Research Objectives

- Motivation for reduced-order modeling of molten-salt natural-circulation systems.
- Role of one-dimensional models in design studies, sensitivity analysis, control, digital twins, and systems-code applications.
- Limitations of conventional globally calibrated one-dimensional models.
- Central hypothesis and research questions.
- Original contributions and division of work among collaborators.
- Scope, limitations, and organization of the thesis.

# 2. Background And Literature Review

Include a brief summary of the state of the art and why it may not be sufficient, or how this work improves it.

## 2.1 Molten-Salt Natural Circulation

- Buoyancy-driven flow and feedback between mass flow, heat transfer, and temperature.
- Low-Reynolds-number and high-Prandtl-number behavior.
- Mixed convection, developing flow, and thermal entrance effects.
- Flow stability, oscillation, and recirculation.
- Brief aside on molten salt reactors, why they are worth pursuing, and how the experiment being modeled and the digital twin being created relate to MSR controls and predictions.

## 2.2 Thermophysical Properties

- HITEC and related molten-salt property models.
- Validity ranges and composition dependence.
- Effects of property selection on Reynolds, Prandtl, Grashof, Rayleigh, Richardson, and Graetz numbers.
- Propagation of property uncertainty into buoyancy, friction, and heat-transfer predictions.

## 2.3 Hydraulic Closures

- Fully developed and developing laminar friction.
- Bends, contractions, expansions, junctions, and component clusters.
- Development-reset distances and close-coupled fittings.
- Limitations of conventional minor-loss coefficients at low Reynolds number.

## 2.4 Thermal Closures

- Internal convection and mixed-convection correlations.
- Wall conduction and conjugate heat transfer.
- Insulation, contact resistance, external convection, and radiation.
- Heater and cooler boundary models.

## 2.5 Reduced-Order And Systems-Code Modeling

- CFD-informed one-dimensional modeling.
- Closure calibration and model-form uncertainty.
- Separation of calibration and evaluation cases, including restrictions on using target-case CFD outputs as predictive model inputs.
- Relationship of the present work to future SAM-facing model construction.

# 3. Physical System, CFD Database, And Evidence Structure

## 3.1 TAMU Natural-Circulation Loop

- Loop geometry, materials, heater, cooler, test section, bends, junctions, and instrumentation.
- Experimental operating conditions and available measurements.
- Measurement limitations and sensor-coordinate mapping.

## 3.2 CFD Database

- OpenFOAM model, boundary conditions, numerical methods, and case families.
- Continuation strategy and identification of usable steady-state intervals.
- Relationship between nominal, perturbed, holdout, and external-evaluation cases.

## 3.3 Evidence Roles

Each case and reduced quantity will be assigned a documented role:

- calibration or training evidence;
- diagnostic evidence;
- holdout evaluation evidence;
- external evaluation or experimental comparison evidence, where available;
- excluded or future-work evidence.

## 3.4 Restrictions On Predictive Model Inputs

To preserve a genuine forward prediction, quantities obtained from the CFD case being predicted will not be supplied to the one-dimensional model as inputs. Examples include:

- CFD mass flow;
- realized CFD wall heat flux;
- realized cooler duty; and
- validation temperatures.

These quantities may be used to diagnose model behavior or replay a known CFD solution, but not to evaluate the forward-predictive capability of the one-dimensional model.

# 4. Three-Dimensional-To-One-Dimensional Reduction Methodology

## 4.1 Loop Segmentation

In this thesis, a leg denotes a major physical portion of the loop, such as the upcomer or downcomer; a segment denotes a one-dimensional subdivision used in the mathematical model; and a component denotes a localized feature such as a bend, junction, heater, cooler, or connector.

Definition of physically meaningful one-dimensional regions, including:

- heater and lower leg;
- upcomer inlet;
- quartz test section;
- upcomer outlet;
- cooler or heat-exchanger legs;
- downcomer;
- bends and corners;
- junctions, stubs, and connectors.

## 4.2 Pressure Reduction

Construction of a segmentwise pressure-balance decomposition containing:

- hydrostatic and buoyancy contributions;
- distributed friction;
- developing-flow and reset effects;
- component-local losses;
- junction losses and leg-specific apparent losses; and
- unresolved pressure residuals.

## 4.3 Thermal Reduction

Construction of a segmentwise heat-balance decomposition containing:

- heater input;
- cooler or heat-exchanger removal;
- fluid-to-wall transfer;
- wall conduction and material resistance terms, with storage reserved for future transient extensions;
- passive environmental heat loss;
- test-section heat balance;
- junction and stub heat transfer; and
- unresolved thermal residuals.

## 4.4 Reduction Consistency

- Sign conventions and coordinate definitions.
- Conservation checks.
- Time-window selection and temporal uncertainty.
- Treatment of nonuniform and multidirectional CFD fields.
- Conditions under which a single loop-wide correction factor is inadequate and leg- or component-specific treatment is required.

# 5. Mathematical Formulation Of The Coupled One-Dimensional Fluid-And-Wall Model

## 5.1 Modeling Assumptions, Variables, And Sign Conventions

- Steady, single-phase modeling assumptions.
- Loop coordinate and positive-flow direction.
- Fluid, wall, and environmental state variables.
- Definitions of segment-averaged pressure, temperature, heat rate, and mass flow.
- Interface and junction conditions.

## 5.2 Governing Conservation Equations

- Overall loop momentum balance.
- Segmentwise fluid energy balance.
- Steady wall and material heat balances.
- Mass and energy continuity at segment interfaces and junctions.
- Coupling among mass flow, temperature-dependent properties, buoyancy, pressure loss, and heat transfer.

## 5.3 Constitutive Relations And Segment Coupling

- Thermophysical-property relations.
- Friction and component-loss relations.
- Internal heat-transfer relations.
- Wall-conduction and external heat-transfer relations.
- Treatment of developing flow, junctions, and recirculation.

## 5.4 Loop Assembly And Numerical Solution

- Assembly of the segment equations into the complete loop model.
- Boundary and continuity constraints.
- Nonlinear solution for mass flow, fluid temperatures, and wall temperatures.
- Convergence criteria and conservation checks.

## 5.5 Segment Metadata

Each segment will contain:

- geometry and orientation;
- material and insulation stack;
- thermal source or sink role;
- hydraulic closure;
- thermal-resistance network;
- development state;
- recirculation or single-stream validity flag;
- uncertainty information; and
- predictive-use status: included, diagnostic, provisional, or excluded.

## 5.6 Candidate Model Forms

- Setup-only baseline model.
- CFD-boundary replay model for diagnosis.
- Segment-only coupled fluid-and-wall model.
- Junction-aware coupled model.
- Hybrid upcomer model with separate throughflow and exchange behavior.
- Frozen predictive model assembled only from predefined setup inputs and closures that satisfy the predictive-use criteria.

# 6. Closure Identification, Error Characterization, And Predictive-Use Criteria

In this thesis, a closure is a constitutive relation or reduced model used to represent a heat-transfer, friction, pressure-loss, or mixing effect that is not resolved directly by the one-dimensional conservation equations.

## 6.1 Closure Identification

- Candidate friction and minor-loss closures.
- Heater and cooler boundary models.
- Passive heat-loss models.
- Internal convection and Nusselt-number models.
- Junction and component-local corrections.
- Hybrid terms for recirculating or multidirectional regions.

## 6.2 Uncertainty Sources

This is not uncertainty propagation, but rather the steps taken to bound error.

- Temporal drift and oscillation.
- Effective sample size and corrected standard error.
- Mesh sensitivity and grid-convergence disposition.
- Thermophysical-property uncertainty.
- Sensor-location and projection uncertainty.
- Boundary-condition uncertainty.
- Model-form uncertainty.

## 6.3 Criteria For Including A Closure In The Predictive Model

A candidate closure will be included in the predictive model only when it has:

- a defined physical role;
- documented units and sign convention;
- a valid geometry and flow-regime range;
- adequate calibration evidence;
- acceptable uncertainty and mesh disposition;
- no prohibited runtime dependence on target CFD outputs;
- acceptable performance on data not used for fitting; and
- a documented failure or fallback condition.

A closure that does not satisfy these criteria will be identified as diagnostic, provisional, excluded, or reserved for future work rather than used in forward predictions.

# 7. Reduced CFD Evidence And Physical Interpretation

## 7.1 Hydraulic Behavior

- Distribution of buoyancy drive and pressure loss around the loop.
- Developing-flow and reset effects.
- Bend, junction, and component-cluster behavior.
- Relationship between hydraulic closure and predicted mass flow.

## 7.2 Thermal Behavior

- Heater and cooler energy balances.
- Passive wall and environmental losses.
- Test-section heat-transfer behavior.
- Junction and stub heat-transfer contributions.
- Separation of internal convection errors from boundary and heat-loss errors.

## 7.3 Upcomer Recirculation

- Evidence for departure from ordinary single-stream pipe behavior.
- Consequences for conventional friction, Nusselt-number, and local-loss interpretations.
- Definition and limitations of the hybrid upcomer representation.
- Identification of operating regions where the available evidence remains insufficient.

# 8. Predictive Model Assessment

Discussion of methods, implementation, how the model is tested, and what it is tested against.

## 8.1 Model-Form Comparison

Comparison of progressively more complete model forms:

- setup-only baseline;
- thermal-boundary replay diagnostic;
- heater and cooler boundary model that satisfies the predictive-use criteria;
- segment-only fluid-and-wall model;
- junction-aware fluid-and-wall model;
- hybrid-upcomer model; and
- frozen final predictive candidate, if all predictive-use criteria are satisfied.

## 8.2 Evaluation Metrics

- Mass-flow error.
- Leg and sensor-temperature error.
- Heat-balance closure.
- Pressure-balance closure.
- Error relative to measurement and temporal uncertainty.
- Generalization from calibration to holdout cases.
- Model complexity and parameter count.
- Compliance with the predefined predictive input set.
- Failure modes and extrapolation behavior.

## 8.3 Interpretation Of Negative Results

Model forms that improve one output while degrading conservation, temperature prediction, or held-out performance will be retained as falsification or diagnostic evidence rather than presented as successful predictive closures.

# 9. Implications, Conclusions, And Future Work

## 9.1 Supported Conclusions

- Physical effects that must be retained locally in a predictive one-dimensional model.
- Conditions under which global correction factors are inadequate.
- Benefits and limitations of junction-aware and hybrid model forms.
- Role of evidence, discipline, and uncertainty in closure selection.

## 9.2 SAM-Facing Interpretation

- Representation of segmentwise pressure losses.
- Explicit segmentwise thermal balances and environmental heat-loss terms.
- Junction and stub ownership.
- Recirculation and validity flags.
- Closure metadata and fallback behavior.

The thesis will explicitly distinguish these recommendations from actual SAM implementation or SAM validation.

## 9.3 Limitations And Future Work

- Additional wall and cooler-side measurements.
- Improved pressure instrumentation around bends and junctions.
- More detailed upcomer recirculation diagnostics.
- Additional mesh and grid-convergence studies.
- Broader experimental validation.
- Transient extension of the steady model.
- Future implementation and validation in SAM.

The final predictive model assessment will distinguish between closures that are admitted into a frozen predictive model and closures that remain diagnostic, provisional, or future work.
