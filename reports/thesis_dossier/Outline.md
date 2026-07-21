---
provenance:
  - reports/thesis_dossier/README.md
  - operational_notes/maps/literature-synthesis-and-gates.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - .agent/BLOCKERS.md
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_parallel_progress_and_next_plan/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_current_context.md
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md
tags: [thesis-dossier, thesis-outline, weekly-presentation, thesis-source, closure-ledger, forward-model, litrev-synthesis, methodology, two-week-plan]
related:
  - reports/thesis_dossier/README.md
  - operational_notes/maps/README.md
  - operational_notes/07-26/13/2026-07-13_CURRENT_CLOSURE_AND_PREDICTIVE_MODEL_START_HERE.md
  - operational_notes/07-26/13/2026-07-13_external_report_research_index_and_blocker_audit.md
task: AGENT-304
date: 2026-07-13
role: Coordinator/Writer
type: report
status: reference
supersedes: []
superseded_by:
---
# Thesis Outline

Tags: #thesis-outline #weekly-presentation #thesis-source #closure-ledger
#forward-model #litrev-synthesis #methodology #two-week-plan

## Working Thesis Direction

- Develop and evaluate a defensible CFD-to-1D closure workflow for the TAMU
  molten-salt natural-circulation loop.
- Use Ethan OpenFOAM CFD as the current high-fidelity reference while being
  explicit that CFD is not experimental validation.
- Move from CFD-informed replay toward a predictive 1D model:
  - physical setup inputs in;
  - predicted mass flow and sensor temperatures out;
  - no runtime use of CFD `mdot`, realized CFD `wallHeatFlux`, or validation
    temperatures in thesis-strength predictive modes.
- Use the steady-state `fluid+walls` model form as the final 1D model target:
  - fluid bulk state plus wall/material stack by segment;
  - segment-local pressure and thermal model slots;
  - source/sink roles, boundary-layer/development state, recirculation flags,
    admission status, and uncertainty status.
- Make the core methodological contribution a branchwise closure ledger rather
  than a single tuned global coefficient.

## Current Section Files

- `reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md`
  - thesis/paper prose for the comprehensive CFD-to-1D modeling approach.
- `reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md`
  - thesis/paper prose for the steady `fluid+walls` model form.
- `reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md`
  - thesis/paper prose for the final split policy and evidence classes.
- `reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md`
  - thesis/paper prose for upcomer recirculation and hybrid-model guardrails.
- `reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md`
  - thesis/paper prose comparing segment-only, junction-aware, and hybrid
    upcomer ledgers.
- `reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md`
  - thesis/paper prose for the endpoint strategy, intermediate model-form
    bakeoff, cost comparison, numerical algorithms, and SAM-facing implications.
- `reports/thesis_dossier/Chapters_and_sections/current/07_wall_test_section_coupled_score_and_physics_plan.md`
  - thesis/paper prose for the coupled wall/test-section negative result and
    next source/temperature-shape physics plan.
- `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md`
  - thesis-critical table mapping every current claim to evidence, split role,
    blocker, figure/table source, and caveat.
- `reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md`
  - one-table loop-region atlas for `fluid+walls` geometry, material stack,
    pressure model, thermal circuit, source/sink role, recirculation,
    uncertainty, and admission status.
- `reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md`
  - chapter package combining time-window, mesh/GCI, property-lane, sensor-map,
    split, runtime-leakage, recirculation, and wall/test-section uncertainty.
- `reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md`
  - SAM-facing interpretation of branchwise pressure losses, heat ledgers,
    recirculation flags, and admission status without claiming SAM validation.
- `reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md`
  - figure brief for segment atlas diagrams, upcomer hybrid schematic,
    junction-aware comparison, model-form ladder, and SAM-facing flowchart.

## Core Goals

- Build a 1D model structure that can predict:
  - loop mass flow rate;
  - branch and sensor temperatures;
  - pressure and heat residual attribution;
  - sensitivity to heater/cooler settings, boundary losses, and property modes.
- Show which CFD-derived closure terms are defensible and which are only
  diagnostic.
- Separate hydraulic, thermal, property, boundary-condition, mesh, and
  steady-state uncertainties so that no model term hides another model error.
- Produce thesis-ready tables that state, for every result:
  - source path;
  - model form;
  - input/output contract;
  - validation/admission status;
  - uncertainty or blocker.

## Model Forms and Input/Output Contracts

### Steady `fluid+walls` Segment Model

- Purpose:
  - represent the loop as a coupled fluid and wall/material segment ledger, not
    a fluid-only balance with fitted heat leaks.
- Segment fields:
  - geometry and station mapping;
  - material stack: steel, insulation, quartz, or connector/junction region;
  - pressure model slot;
  - thermal circuit slot;
  - heater, cooler/HX, passive wall, test-section, or junction source/sink role;
  - boundary-layer/development state;
  - recirculation and coefficient-label flags;
  - admission and uncertainty status.
- Steady fluid energy balance:

```text
d/ds[ mdot cp(T) T ] =
    q'_heater_to_fluid,i
  - q'_cooler_removed,i
  - q'_wall_loss,i
  + q'_other_source_to_fluid,i
```

- Wall-loss circuit for ordinary pipe/wall-covered regions:

```text
fluid bulk
  -> internal convection / thermal boundary layer
  -> pipe wall conduction
  -> insulation or local material layer
  -> external convection to ambient
  -> external radiation to surroundings
```

- Test-section contract:
  - the test section is the bare-quartz middle upcomer span, not a removable
    model artifact;
  - net test-section heat can be positive or negative and should be computed
    from electrical deposition and quartz-to-ambient loss:

```text
q'_test_section_to_fluid =
    q'_electrical_deposition_to_fluid_or_wall
  - (T_drive - T_external_drive) / R'_quartz_external
```

- Guardrail:
  - do not include wall storage or transient heat-capacity terms in the current
    steady-state thesis model unless a later dated note reopens transient work.

### 1D Forward Predictive Model

- Purpose:
  - predict `mdot` and TP/TW/sensor temperatures from setup inputs.
- Runtime inputs:
  - geometry and branch/station map;
  - fluid property mode;
  - heater electrical/setup inputs;
  - cooler/HX setup inputs;
  - external boundary conditions: `Ta`, `Tsur`, emissivity, wall/external
    hA/UA/layer parameters where admitted;
  - branch/fitting loss model coefficients that were trained only on allowed
    training rows.
- Outputs:
  - predicted `mdot`;
  - predicted branch temperatures and TP/TW sensor temperatures;
  - predicted pressure losses by branch/section;
  - predicted heat removal/addition by heater, cooler, passive loss, radiation,
    and residual lanes;
  - final-training, support, testing/holdout, and external-test score tables.
- Guardrail:
  - any mode using CFD `mdot`, realized CFD `wallHeatFlux`, or validation
    temperatures at runtime is diagnostic, not predictive.

### Hydraulic Closure Ledger

- Model form:
  - buoyancy drive is a loop integral over local temperature, density, pressure,
    and elevation, not a global `mdot`-only term:

```text
Delta p_drive =
  integral_loop rho(T(s), p(s), composition, property_lane) g dz(s)
```

  - pressure loss is a sum of segment-local distributed, reset/development,
    local-K, branch/junction, and residual terms:

$$
\Delta p_{loss} =
  \sum_i [
    f_i(Re_i, Pr_i, Ri_i, regime_i, roughness_i, geometry_i) (L_i/D_i) *q_i
    + K_i(local_geometry_i, reset_i, development_i, regime_i) q_i
  ]
$$

  - older compact ledger shorthand remains useful only as a taxonomy:
    `dp = dp_hyd + dp_kin + dp_dist_dev + dp_minor + dp_reset + dp_res`.
- Candidate terms:
  - fully developed `f_D = 64/Re` as reference only;
  - Shah/Muzychka-Yovanovich developing/friction forms where source-bounded;
  - pressure-derived `f_D,Delta_p` for isolated straight sections;
  - component `K`, cluster `K`, or branch-apparent loss when plane placement
    does not isolate a single fitting.
- Inputs:
  - local density/viscosity;
  - branch geometry and `L/D`;
  - pressure basis and tap/plane placement;
  - local bulk velocity or mass flow;
  - reset distance from bends, reducers, tees, wall material changes, heater,
    and cooler starts.
- Outputs:
  - branch/section pressure loss;
  - fit-safe rows versus diagnostic rows;
  - mdot correction candidate for forward model.

### Thermal Closure and Heat-Loss Ledger

- Model form:
  - heat balance separated into internal convection, wall conduction,
    contact/insulation, external convection, radiation, cooler/HX removal,
    heater-to-salt transfer, wall/storage, and residual.
- Candidate internal `Nu`/HTC forms:
  - fully developed reference `Nu`;
  - forced developing `Nu`;
  - Chen 2017 low-Re molten-salt mixed-convection candidate only where the
    source envelope overlaps TAMU branch conditions;
  - CFD-derived effective `Nu_i` or `UA'` only when mesh/sign/heat-loss gates
    allow it.
- Inputs:
  - `Re`, `Pr`, `Gr`, `Ri`, `Ra`, `Gz`, `L/D`, orientation, heating/cooling
    sign;
  - wall and bulk temperature definitions;
  - external boundary dictionary and radiation policy;
  - heater/cooler setup model.
- Outputs:
  - branch heat gain/loss;
  - internal HTC/Nu diagnostic or admitted rows;
  - passive/cooler/radiation residual attribution;
  - sensor-temperature predictions.
- Guardrail:
  - internal `Nu` must not absorb passive loss, jacket/cooler duty, radiation,
    or heater efficiency errors.

### Property Mode Ledger

- Model form:
  - named property modes rather than one implicit HITEC property set.
- Modes to keep distinct:
  - Reis/Jadyn replication mode;
  - Sohal/Janz density-viscosity mode;
  - Jin viscosity candidate;
  - alternate `cp` cases such as `1424`, `1560`, Sohal/Parida-Basu;
  - Santini/constant thermal conductivity cases.
- Inputs:
  - temperature-dependent or constant property definitions;
  - branch temperature used for property evaluation.
- Outputs:
  - changes in `Re`, `Pr`, `Gz`, buoyancy head, pressure residual, heat residual,
    mdot, and admission status.
- Guardrail:
  - choose/report property lane before fitting friction or heat residuals.

## Methodology Chapter Outline

- Define case families and evidence hierarchy:
  - mainline Salt/Jin continuations;
  - Salt-Q perturbations as sensitivity/correlation-support rows;
  - Kirst rows as historical unless explicitly re-admitted;
  - corrected-Q rows admitted only after row-specific convergence/admission
    checks.
- Define 3D-to-1D reduction:
  - branch map, station map, and geometry provenance;
  - plane/patch/segment definitions;
  - pressure basis: `p_rgh`, static/corrected pressure, total pressure, dynamic
    pressure, hydrostatic and kinetic corrections;
  - wall heat flux and patch role semantics;
  - sensor mapping and TP/TW coordinate uncertainty.
- Define time and admission gates:
  - steady-state final-window metrics;
  - time-series uncertainty, drift, oscillation, corrected SEM;
  - terminal harvest versus runtime stop;
  - closure-fit admissible versus diagnostic/context-only.
- Define mesh and reconstruction gates:
  - coarse/medium/fine availability;
  - GCI readiness and non-monotone/oscillatory rejection;
  - reconstructed-`T` repair status;
  - thermal sign and heat-balance admission.
- Define validation split:
  - final training/calibration: admitted Salt1-4 nominal rows;
  - training support: admitted Salt1 +/-10Q and Salt4 +/-5Q rows with legal-use
    labels preserved;
  - holdout/testing: Salt2 +/-5Q after PM5 extraction repair and admission;
  - external test: `val_salt2` after matching heat-loss/admission package;
  - future holdout: Salt2/Salt4 +/-10Q after terminal harvest/admission and new
    CFD rows after staging, completion, and admission.
- Define scoring:
  - mdot error;
  - pressure residual movement;
  - branch/sensor temperature error;
  - heat residual attribution;
  - model complexity and fitted-versus-validation separation.

## Thesis Endpoint And Model-Form Bakeoff Plan

The preferred endpoint is a fully admitted final predictive 1D model. The
minimum defensible endpoint is a scored and fully explained ladder of model
forms that shows what each added piece of physics buys, what each form requires,
and which rows are predictive, diagnostic, blocked, or future-work.

The canonical final predictive split is locked:

- final training/calibration: `salt1_nominal`, `salt2_jin_nominal`,
  `salt3_jin_nominal`, and `salt4_nominal`;
- training support: `salt1_lo10q`, `salt1_hi10q`, `salt4_lo5q`,
  `salt4_hi5q`;
- holdout/testing: `salt2_lo5q`, `salt2_hi5q`;
- external test: `val_salt2`;
- future holdout candidates: Salt2/Salt4 +/-10Q and new CFD only after
  terminal harvest and admission.

The model-form ladder to compare in the thesis is:

- M0 setup-only baseline;
- M1 CFD thermal-boundary replay diagnostic;
- M2 admitted heater+cooler boundary model;
- M3 segment-only `fluid+walls`;
- M4 junction-aware `fluid+walls`;
- M5 hybrid throughflow plus recirculation-cell upcomer model;
- M6 frozen final predictive candidate, if admission gates pass.

For each form, the thesis should include a table covering equations, runtime
inputs, forbidden runtime inputs, CFD postprocessing requirements, training
rows, score rows, training computational cost, operational runtime cost,
admission status, and expected failure modes. This comparison should appear in
the main methodology/results narrative if space allows and at minimum in an
appendix.

The numerical-methods section should describe the steady nonlinear network
solve: mass-flow and segment-temperature unknowns, pressure and energy
residuals, wall thermal-circuit equations, property updates, pressure/thermal
coupling, root-solve or Newton-like iteration, convergence checks, finite-output
guards, frozen-candidate scoring, and runtime-leakage audits. It should also
explain that this is a reduced-order network/control-volume balance, distinct
from 3D finite volume CFD, finite-element weak-form discretizations, and SAM's
production systems-code implementation.

The SAM-facing section should present the contribution as transferable closure
discipline rather than direct SAM validation: branchwise loss ledgers,
fluid+wall thermal circuits, junction/stub ownership, recirculation flags, and
coefficient admission/uncertainty status can inform SAM model construction and
closure selection.

## Literature Review Outline

### Motivation and Physical Context

- Natural circulation in molten-salt loops.
- Low-flow mixed convection, buoyancy, recirculation, and nonuniform heating.
- Why a 1D predictive model is useful but dangerous without closure discipline.

### HITEC Property Models

- Reis/Jadyn replication properties.
- Sohal/Janz molten-salt database.
- Jin viscosity measurements.
- Parida/Basu and other `cp` alternatives.
- Santini/Nunes/Serrano-Lopez conductivity/property review context.
- Required thesis point:
  - properties are model choices and sensitivity axes, not bookkeeping.

### Friction and Developing Flow

- Fully developed laminar reference: `f_D = 64/Re`.
- Shah and London / Shah entry-length concepts.
- Muzychka-Yovanovich developing pressure-drop forms.
- Why fully developed formulas are references unless reset/development evidence
  supports active use.

### Minor Losses, Fittings, and Reset Distances

- Bends, reducers, expansions/contractions, quartz transitions, tees.
- Lin measurement-method reviews.
- Patino-Jaramillo tee coefficients.
- Salehi close-coupled elbows.
- Required thesis point:
  - fittings are both losses and reset features; do not hide them in global
    friction.

### Internal Heat Transfer

- Fully developed `Nu` references.
- Forced developing internal convection.
- Low-Re molten-salt mixed convection: Chen 2017 as conditional candidate.
- Chen multi-sided heating, Yang inclined-tube, Tian cooled-tube sources as
  diagnostics unless source envelope overlaps TAMU conditions.
- Required thesis point:
  - branchwise `Re/Pr/Gr/Ri/Ra/Gz/L/D` gates before promoting `Nu`.

### Heat Loss, External Boundaries, and Radiation

- VDI Heat Atlas resistance-network framing.
- Heater, cooler/HX, passive convection, wall conduction/storage, contact,
  insulation, radiation.
- Reis heater-failure/solidification context for separating transients and
  storage from steady closure.
- Required thesis point:
  - heat loss is a network, not a cleanup multiplier.

### CFD-to-1D Reduction and Validity Limits

- CFD extraction of section coefficients.
- Plane placement and pressure basis naming.
- Reverse-flow and secondary-flow diagnostics.
- Podila/Csizmadia-Hos context for CFD-derived coefficient limits.
- Required thesis point:
  - universal `f`, `K`, or `Nu` names are invalid when section flow is
    recirculating or not isolated.

### Reduced-Order and Future Predictive Models

- ROM/POD literature as future method, not a current validation claim.
- Snapshot/archive requirements.
- Withheld validation and stabilization requirements.

## Thesis Chapter Outline

### Chapter 1: Introduction

- State the engineering problem:
  - predictive modeling of the TAMU molten-salt natural-circulation loop.
- State the modeling challenge:
  - CFD is rich but expensive; 1D is useful but closure-sensitive.
- State the contribution:
  - a provenance-controlled CFD-to-1D closure ledger and forward-predictive
    model pathway.
- State the central research questions:
  - Which closure terms can be extracted from CFD defensibly?
  - Which literature closures overlap TAMU conditions?
  - What physical submodels dominate predictive error?
  - What can be predicted now, and what remains diagnostic?

### Chapter 2: Literature Review

- Follow the literature outline above.
- End with the branchwise closure ledger as the synthesis.
- Include a table mapping source families to:
  - model form;
  - inputs;
  - outputs;
  - validity envelope;
  - TAMU use status: reference, active candidate, diagnostic, rejected, future.

### Chapter 3: CFD Cases, Data Reduction, and Admission

- Describe Ethan CFD cases and continuation policy.
- Describe current mainline Salt/Jin case family and Salt-Q perturbation role.
- Document steady-state/time-window gates.
- Document case admission classes:
  - thesis-ready;
  - caveated;
  - diagnostic;
  - blocked.
- Include stopped/continued sbatch provenance where relevant.

### Chapter 4: 3D-to-1D Reduction Methodology

- Geometry and branch/station definitions.
- Pressure reduction:
  - segment-resolved buoyancy integral;
  - hydrostatic, kinetic, straight-pipe, reset/development, fitting/cluster,
    junction, recirculation, and residual terms.
- Heat reduction:
  - wallHeatFlux, patch roles, heater/cooler/passive/radiation lanes.
- Junction-aware reduction:
  - compare segment-only and junction-aware ledgers;
  - show how junction/stub heat residuals shift when local roles are separated;
  - keep corner-K as diagnostic until pressure subtraction/admission gates pass.
- Sensor mapping:
  - TP/TW definitions and coordinate uncertainty.
- Validity diagnostics:
  - recirculation, reverse-flow, secondary-flow, wall-flux skew.

### Chapter 5: Hydraulic Closure and Mass-Flow Prediction

- Compare reference friction forms.
- Present pressure ledger and named losses.
- Present upcomer recirculation and onset limits.
- Present hydraulic correction candidates for forward mdot prediction.
- Explain what is fit-safe versus diagnostic.

### Chapter 6: Thermal Boundary, Heat-Loss Separation, and Internal HTC

- Present external boundary/radiation correction:
  - `rcExternalTemperature` includes emissivity/Tsur effects in realized
    `wallHeatFlux`.
- Present steady `fluid+walls` thermal circuits:
  - heater electrical-to-fluid entry;
  - cooler/HX removal;
  - passive wall loss;
  - bare-quartz test-section heat/loss balance;
  - wall/layer resistance;
  - junction/stub/connector heat-loss or mixing residual lanes.
- Present internal HTC/Nu only as admitted or diagnostic depending on
  mesh/sign/heat-loss gate status.
- Emphasize that cooler/HX is currently the first-order thermal lever.

### Chapter 7: Uncertainty, Mesh, and Trust Boundaries

- Time-series steady-state uncertainty.
- Mesh/GCI readiness, final-use disposition, and future coefficient gates.
- Reconstructed-`T` repair status.
- Property sensitivity.
- Sensor-map status and TP/TW projection caveats.
- Split uncertainty and runtime-leakage uncertainty.
- Claim ledger and admission classes.
- Source file: `reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md`.

### Chapter 8: Forward Predictive 1D Model

- Input contract.
- Final split:
  - train/calibrate across admitted Salt1-4 nominal rows;
  - test on admitted perturbation, external, and new-CFD rows.
- Forward-v0 diagnostic results.
- Hydraulic correction path.
- Heater and cooler/HX admitted boundary submodels.
- Wall/test-section/passive-boundary model blocker.
- M3+TS successor:
  - heater model + cooler/HX model + explicit setup-only distributed
    test-section heat-loss model;
  - compare against diagnostic M2/M3 without deleting test-section physics.
- External-boundary and `fluid+walls` segment dictionary path.
- End-to-end scorecard structure.
- State what is predictive now versus still diagnostic.
- Use `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md`
  to keep result claims tied to evidence, split role, blocker, source, and
  caveat.
- Use `reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md`
  as the segment implementation and admission-status table.
- Use `reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md`
  for systems-code implications without claiming SAM validation.
- Use `reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md`
  for the thesis figure package: segment atlas, upcomer hybrid, junction-aware
  comparison, model-form ladder, and SAM-facing flowchart.

### Chapter 9: Conclusions and Future Work

- Summarize supported claims.
- Summarize unresolved blockers.
- Recommend experiments:
  - pressure taps around fitting/quartz clusters;
  - wall/surface/coolant temperature instrumentation;
  - coolant-side HX/cooler measurements;
  - startup/transient measurements if in scope.
- Recommend future modeling:
  - conformal/refined mesh repair;
  - radiation-separable or CHT boundary studies;
  - ROM snapshot design after full-order closure stabilizes.

## Research Avenues Organized Logically

### A. Evidence and Admission Infrastructure

- State:
  - generated index, blocker register, and topic maps now exist.
- Thesis value:
  - makes claims auditable and prevents stale blockers from re-entering the
    story.
- Next product:
  - claim ledger table with thesis-ready/caveated/diagnostic/rejected status.
  - Current source: `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md`.

### B. Literature-Gated Closure Ledger

- State:
  - five lit-review gate packages exist: source envelope, property sensitivity,
    reset/named losses, heat-loss calibration, CFD validity diagnostics.
- Thesis value:
  - turns literature review into model admission rules.
- Next product:
  - chapter-ready source-family table: author/title, equation family, inputs,
    outputs, TAMU overlap, and use status.

### C. Hydraulic Closure and Mdot Prediction

- State:
  - forward-v0 overpredicts mdot; hydraulic correction must precede thermal
    fitting.
  - F6 remains open but narrowed; current PM5 rows are recirculation diagnostics
    and production remains `F3_shah_apparent`.
- Model forms:
  - segment-resolved buoyancy-drive and pressure-loss ledger;
  - fit-safe straight-section friction;
  - named component/cluster losses;
  - possible Re/buoyancy correction candidate only after non-recirculating or
    explicitly recirculation-modeled evidence exists.
- Next product:
  - final-split mdot score after hydraulic-only correction.

### D. Thermal Boundary and Heat-Loss Separation

- State:
  - cooler/HX dominates current thermal replay error;
  - radiation is embedded in CFD `rcExternalTemperature` wall heat flux;
  - heater and cooler/HX setup-only submodels are admitted as boundary evidence;
  - wall/test-section/passive-boundary heat loss remains the active blocker.
- Model forms:
  - heater efficiency / electrical-to-fluid source contract;
  - constant-UA or epsilon-NTU cooler/HX model;
  - external boundary table with h/Ta/Tsur/emissivity/layer terms;
  - steady `fluid+walls` wall/layer circuit;
  - test-section bare-quartz source/loss balance.
- Next product:
  - M3+TS / `fluid+walls` thermal score with no diagnostic CFD leakage.

### E. Internal HTC/Nu and Mixed Convection

- State:
  - internal HTC/Nu is not allowed to absorb heat-loss residuals;
  - Chen 2017 and other `Nu` forms are conditional on source-envelope overlap;
  - thermal mesh/sign gates remain limiting.
- Model forms:
  - fully developed reference `Nu`;
  - forced developing `Nu`;
  - mixed-convection candidate only if source bounded;
  - CFD effective `Nu_i` as diagnostic/admitted depending on gates.
- Next product:
  - branchwise HTC/Nu bakeoff table after thermal mesh/sign gate.

### F. Mesh, GCI, and Uncertainty

- State:
  - "no mesh for GCI" is stale;
  - `closure-qoi-mesh-gci` is resolved by final-use disposition for current
    non-upcomer final-use rows, not by new publication-grade coefficient
    admission;
  - future coefficient rows still need local uncertainty/admission gates.
- Model forms:
  - GCI triplet only when monotone/defensible;
  - otherwise diagnostic mesh sensitivity.
- Next product:
  - final-split thermal mesh/sign/admission table and clear nonclaim language
    for rows that remain diagnostic.

### G. Sensor and Presentation Scoring

- State:
  - TP/TW mapping is being separated into runtime inputs versus validation
    targets.
- Model forms:
  - sensor map contract with coordinate uncertainty and target definitions.
- Next product:
  - scorecard columns for mdot, branch Tmean, TP, TW, pressure residual, and
    heat residual.

### H. Experimental Upgrade and Future Validation

- State:
  - CFD reference is useful but not experimental validation.
- Future measurements:
  - pressure taps around quartz/fitting clusters;
  - wall/surface/coolant temperatures;
  - coolant-side HX flow/temperature;
  - heater-to-salt transfer measurements;
  - transient/startup data if thesis expands beyond steady closure.

## What We Can Achieve in the Next Two Weeks

Status note as of 2026-07-17: the items below are a planning scaffold from the
July 13 outline. Several have moved: Salt1 is admitted and schema-promoted,
the final split policy changed, heater/cooler boundary submodels are admitted
as boundary evidence, `fluid+walls` is the current model-form target, and the
open blocker set is now `predictive-wall-test-section-submodels`,
`upcomer-onset-data-sparsity`, and `f6-friction-re-correction`.

### Week 1: Make the Predictive Story Coherent

- Complete the active parallel predictive lanes:
  - full `solve_case` confirmation for forward-v0;
  - hydraulic correction candidates and mdot rescore;
  - sensor map contract;
  - end-to-end scorecard precursor.
- Freeze a current model taxonomy:
  - diagnostic replay;
  - CFD-informed replay;
  - predictive setup-only mode;
  - closure-fit/admitted versus context-only rows.
- Produce a thesis-facing model form table:
  - term;
  - equation family;
  - inputs;
  - outputs;
  - training data;
  - final-training, testing/holdout, and external-test status;
  - blocker.
- Write a weekly presentation deck outline:
  - goal and thesis question;
  - why global coefficients are wrong;
  - current predictive input contract;
  - cooler/HX lever;
  - mdot hydraulic blocker;
  - next steps and risk table.

### Week 1 Acceptance Signal

- A forward-model scorecard exists even if it contains blocked rows.
- The scorecard separates:
  - mdot error;
  - branch temperature error;
  - sensor error;
  - pressure residual;
  - heat residual;
  - diagnostic CFD leakage.
- Every major result has a provenance path and admission status.

### Week 2: Convert Progress into Thesis-Ready Structure

- Draft thesis Chapter 1 bullet prose:
  - motivation;
  - research questions;
  - contributions;
  - claim boundaries.
- Draft Chapter 2 literature-review table:
  - source family;
  - model form;
  - input/output variables;
  - source envelope;
  - TAMU overlap;
  - use status.
- Draft Chapter 3/4 methods scaffold:
  - case admission;
  - 3D-to-1D reduction;
  - pressure and heat ledgers;
  - validation split;
  - uncertainty gates.
- Prepare current-results figures/tables:
  - branchwise closure ledger diagram;
  - model input/output diagram;
  - pressure ledger figure;
  - heat-loss pathway figure;
  - predictive scorecard table;
  - blocker/status table.
- Decide, explicitly, what the thesis can claim if no new simulations finish:
  - defensible methodology and diagnostic predictive pathway;
  - not final validated predictive 1D model unless held-out scoring and
    hydraulic/thermal gates pass.

### Week 2 Acceptance Signal

- A committee-ready outline exists with:
  - chapter bullets;
  - key figures/tables;
  - supported claims;
  - caveated claims;
  - blockers and next experiments.
- The weekly presentation can be assembled directly from the dossier without
  reading chat history.

## Near-Term Thesis Claims to Aim For

- Strong claim:
  - a branchwise, provenance-controlled closure ledger is necessary for this
    loop and is better supported than global correction factors.
- Strong claim:
  - the current CFD-to-1D thermal mismatch is dominated by boundary/HX/heat-loss
    representation before internal `Nu` fitting should be trusted.
- Strong claim:
  - realized CFD `wallHeatFlux` includes `rcExternalTemperature` radiation
    effects, so radiation-off replay is sensitivity, not parity.
- Moderate claim:
  - pressure-rooted hydraulic corrections are required before thermal predictive
    fitting because current forward-v0 overpredicts mdot.
- Moderate claim:
  - the final predictive model should use admitted Salt1-4 nominal rows for
    training/calibration and reserve perturbation, external, and new CFD rows
    for testing and holdout.
- Moderate claim:
  - literature model forms can be made operational through source-envelope,
    property, reset, heat-loss, and CFD-validity gates.
- Caveated claim:
  - heater and cooler/HX setup-only submodels are admitted as boundary evidence,
    but wall/test-section/passive-boundary heat loss still blocks final
    predictive promotion.
- Caveated claim:
  - internal HTC/Nu values are useful diagnostics but need mesh/sign/heat-loss
    admission before thesis-strength closure fitting.
- Future-work claim:
  - experimental pressure taps, wall/surface/coolant measurements, and
    coolant-side HX data are the highest-value measurements for reducing model
    ambiguity.

## Suggested Weekly Presentation Outline

- Slide 1: Goal and thesis question.
- Slide 2: Why a branchwise closure ledger is needed.
- Slide 3: Model input/output contract.
- Slide 4: Literature gates that control model admission.
- Slide 5: Current CFD-to-1D reduction method.
- Slide 6: Hydraulic finding: mdot overprediction and pressure-ledger path.
- Slide 7: Thermal finding: cooler/HX boundary is first-order.
- Slide 8: Boundary/radiation correction: `rcExternalTemperature` policy.
- Slide 9: Current blockers and stale blockers that are resolved.
- Slide 10: Two-week plan and expected thesis deliverables.
