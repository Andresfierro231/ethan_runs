---
provenance:
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/ethan_literature_gap_requests.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/ethan_external_literature_request_checklist.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/ethan_model_context_inventory.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/ethan_branch_closure_gap_matrix.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/ethan_negative_model_evidence.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/notes/HITEC_PROMPT7_MODELING_DISCOVERIES_AND_NEXT_STEPS.md
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_model_form_hierarchy.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_active_equation_gate_matrix.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_property_gate_matrix.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_Nu_correlation_gate_matrix.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_minor_loss_K_gate_matrix.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_CFD_to_network_methodology.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_pressure_energy_accounting_rules.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_unresolved_claims.csv
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/data/audit_outputs/final_release/HITEC_final_source_gaps.csv
tags: [report, litrev, model-forms, source-gates, pressure-ledger, heat-loss, topology]
related:
  - .agent/status/2026-07-22_TODO-LITREV-LATEST-MODELING-HANDOFF-2026-07-22.md
  - .agent/journal/2026-07-22/litrev-latest-modeling-handoff.md
  - imports/2026-07-22_litrev_latest_modeling_handoff.json
  - operational_notes/START_HERE_FOR_AGENTS.md
  - operational_notes/maps/README.md
  - operational_notes/maps/literature-synthesis-and-gates.md
  - operational_notes/maps/forward-predictive-model.md
  - reports/thesis_dossier/README.md
task: TODO-LITREV-LATEST-MODELING-HANDOFF-2026-07-22
date: 2026-07-22
role: Writer
type: report
status: complete
---
# Litrev Latest Modeling Handoff

Date: 2026-07-22

Findability links were added to:
`operational_notes/START_HERE_FOR_AGENTS.md`,
`operational_notes/maps/README.md`,
`operational_notes/maps/literature-synthesis-and-gates.md`,
`operational_notes/maps/forward-predictive-model.md`, and
`reports/thesis_dossier/README.md`.

This report translates the latest source-audited HITEC literature review into
modeling guidance for the Ethan 1D/3D work. It does not promote any Ethan CFD
or 1D trial result to literature evidence. It identifies what the litrev says is
source-supported, what remains source-bounded or diagnostic, what Ethan had
asked for as extra research, and what should be tried next in the main modeling
work.

## Executive Takeaway

The latest litrev points to one conservative near-term modeling architecture:
MF-01, a gated segmentwise single-stream developing-flow network. It rejects a
loop-wide friction multiplier, one global UA, universal constant fitting K
values, and fully developed defaults as production closures. The model should
carry pressure, energy, property, geometry, development/reset, topology, and
source-envelope state for every segment.

The strongest immediate coding target is a case-by-segment admission engine. It
should compute nondimensional groups, compare them against source envelopes,
apply pressure and energy accounting rules, and label candidate closures as
active, source-bounded, diagnostic, appendix-only, rejected, or unresolved.

## Ethan-Requested Extra Research Identified

The litrev contains a dedicated Ethan research-request register. These are the
fourteen wanted extra research threads, ordered by practical modeling impact.

| ID | Priority | Needed research | Why it matters for modeling |
| --- | --- | --- | --- |
| ETH-GAP-001 / ELR-001 | High | Variable-density natural-circulation pressure-budget reduction. | Pressure-derived friction and K rows cannot be promoted unless hydrostatic, kinetic, distributed, reset, feature, and residual terms are separated without buoyancy double counting. |
| ETH-GAP-002 / ELR-002 | High | Component versus cluster losses and pressure-recovery planes. | Corner/two-tap rows must stay section-effective unless plane placement, recovery, basis, and isolation support a component K. |
| ETH-GAP-003 / ELR-003 | Medium | Straight/developing-reference subtraction for short feature spans. | Short tap spans can create negative or upper-bound K values if straight/developing loss subtraction is not source-bounded. |
| ETH-GAP-004 / ELR-004 | High | Reverse-flow topology and single-stream rejection criteria. | Upcomer HTC/friction reductions are invalid as ordinary one-stream closures when persistent reverse area/mass fractions exist. |
| ETH-GAP-005 / ELR-005 | Medium | Exchange-cell or compartment models for recirculating throughflow. | If one bulk state fails, the next model form needs source-supported state variables, exchange mass flow, residence time, energy closure, and calibration data. |
| ETH-GAP-006 / ELR-006 | High | OpenFOAM `rcExternalTemperature` radiation and heat-flux accounting. | Do not add a separate radiation term on top of CFD `wallHeatFlux` unless the boundary-condition semantics prove radiation is excluded. |
| ETH-GAP-007 / ELR-007 | High | Fused-quartz emissivity/transmissivity and exposed-section radiation. | The quartz test section should not be collapsed into an insulated stainless branch or treated as radiation-negligible without a bound. |
| ETH-GAP-008 / ELR-008 | High | Segmented heat-loss network and cooler UA calibration. | Internal Nu cannot absorb heater efficiency, passive loss, radiation, storage, or cooler mismatch. |
| ETH-GAP-009 / ELR-009 | Medium | CFD-to-1D geometry, station, branch, and heat-loss reduction. | Mesh/span truth, 1D geometry, station maps, and reduced branch values must stay provenance-labeled. |
| ETH-GAP-010 / ELR-010 | Medium | CFD-informed closure admission and calibration transfer. | CFD-fitted coefficients need calibration/validation split, transfer rule, uncertainty, and rejection criteria before reuse. |
| ETH-GAP-011 / ELR-011 | High | Source-envelope and property carryforward in closure scorecards. | A closure row should not pass if source-validity envelope, property source, and transfer limits are blank or incompatible. |
| ETH-GAP-012 / ELR-012 | High | Same-QOI CFD uncertainty for derived coefficients. | Mesh/time uncertainty must target the exact postprocessed coefficient, Nu, HTC, UA, heat flux, or pressure drop used by the 1D model. |
| ETH-GAP-013 / ELR-013 | Medium | Multi-QOI validation and compensating-error checks. | Global mass-flow agreement alone can hide pressure-budget and thermal-boundary errors. |
| ETH-GAP-014 / ELR-014 | Medium | HITEC property provenance and facility property candidates. | Jin viscosity and Parida/Basu/manufacturer heat capacity remain source-gated until primary provenance and uncertainty are resolved. |

## Model Forms To Carry Forward

### MF-01: Gated Single-Stream Developing Segment Network

Use this as the first production architecture.

Pressure ledger:

```text
Delta p_static =
  Delta p_hyd
  + Delta p_kin
  + Delta p_dist,dev
  + Delta p_minor/section
  + Delta p_reset
  + Delta p_transient
  + Delta p_res
```

Energy ledger:

```text
Q_loop =
  Q_heater_to_salt
  - Q_jacket
  - Q_passive
  - Q_storage
  - Q_res
```

Core segment gates:

```text
Re = rho |U| D_h / mu
Pr = mu c_p / k
Gr = g beta DeltaT D_h^3 / nu^2
Ri = Gr / Re^2
Ra = Gr Pr
Gz = Re Pr D_h / x_t
```

Add topology diagnostics:

```text
F_A = area(u_n < 0) / A
F_m = integral_{u_n < 0}(rho |u_n| dA) / integral_A(rho |u_n| dA)
S_sec = sqrt(<u_perp^2>_A) / |u_m|
```

MF-01 can predict branchwise steady or quasi-steady pressure drop, mass flow,
bulk temperature, developing friction, developing heat transfer, and residuals.
It cannot represent resolved counterflow topology, recirculation residence time,
bistable exchange, or arbitrary startup oscillations.

### MF-02: Section/Cluster Losses Before Component K

Use section or cluster loss naming first:

```text
Delta p_loss =
  Delta p_meas_or_CFD
  - Delta p_straight,dev
  - Delta p_kin
  - Delta p_hyd
```

Then, only if evidence supports the normalization:

```text
Delta p_sec = K_sec rho U_ref^2 / 2
```

If multiple fittings, incomplete recovery, recirculation, or tap-span ambiguity
are included, call it `K_cluster`, `section apparent loss`, or
`CFD-informed section loss`, not universal component K.

### MF-03: Three-Node Signed-Flow Junction Network

Use only when a modeled branch or junction path has negative net flow or
topology-dependent redistribution that a one-node junction cannot capture. This
handles signed network paths, not simultaneous forward/reverse motion inside
one cross-section.

### MF-04: Throughflow Plus Recirculation Cell

Use only after persistent coherent recirculation invalidates MF-01 and the cell
partition is calibrated. Candidate energy form:

```text
rho V_r c_p dT_r/dt = mdot_ex c_p (T_main - T_r) + Q_r
```

This is a TAMU-calibrated model-form candidate. Two-fluid exchange-flow
equations remain appendix-only analogies and should not be used as active
single-fluid HITEC flux laws.

### MF-05: Period-Averaged Unsteady Fitting Loss

Keep appendix-only unless the case is positive-direction, periodic,
approximately sinusoidal, topology-preserving, and within the source envelope.
Do not use it for startup, reversal, or arbitrary natural-circulation
oscillations.

### MF-06: ROM / Compartment / POD Hybrid

Delay until the full-order model is verified and validated. A ROM claim needs
snapshot variables, parameter bounds, basis construction, mode criterion,
projection or stabilization method, held-out validation metrics, and
extrapolation flags.

## Closure-Specific Latest Findings

### Properties

Use these as the current property hierarchy:

| Property | Litrev gate | Modeling decision |
| --- | --- | --- |
| Density | PASS | Use Sohal/INL `rho = 2293.6 - 0.7497 T_K`; record composition and salt-age metadata. |
| Thermal expansion | PASS | Compute `beta = 0.7497 / rho(T)` from the selected density model. |
| Viscosity | PASS WITH GUARD | Use Sohal/INL full-precision polynomial only with range and nonpositive guards; run Jin/Sohal sensitivity until final property mode is selected. |
| Heat capacity | PASS AS SENSITIVITY | Keep `c_p = 1560 J/kg-K` and alternatives as sensitivity, not a definitive source truth. |
| Thermal conductivity | PASS WITH SENSITIVITY | Use Santini quadratic candidate and run conductivity sensitivity, because `k` drives `Pr`, `Gz`, `Nu`, and heat-loss inference. |
| Freeze/stability limits | PASS AS SAFETY/OPERATING METADATA | Track batch/age/cover gas and freeze margin; do not treat fresh-eutectic values as universal. |

Rejected property equations remain rejected: Reis rounded viscosity, Chen printed
thermal-conductivity `T^3`, and Wu printed viscosity sign.

### Friction And Development

`f_D = 64/Re` is only a fully developed laminar circular-pipe reference. It is
not an active default after bends, junctions, area changes, thermal resets, or
buoyancy/redevelopment. Use Shah apparent entry pressure and
Muzychka/Yovanovich developing pressure-drop architecture as the source-bounded
starting point, with explicit reset distances and Darcy/Fanning convention
labels.

### Internal Heat Transfer

`Nu = 4.36` is a reference limit only. The active heat-transfer closure should
be chosen segmentwise.

The strongest forced/developing candidate is Muzychka/Yovanovich combined-entry
Nu when mixed convection and topology gates are inactive. The strongest
low-Re molten-salt laminar mixed-convection candidate is Chen 2017:

```text
Nu = 1.847 (mu_b/mu_w)^0.14
     [Gz + 0.076 (Gr Pr D/L)^0.765]^(1/3)
```

but only if the TAMU segment envelope overlaps the source range:
`Re = 300-2300`, `Pr = 11-27`, `Gr = 8.56e4-3.95e6`,
`Gz = 150-310`, and `35 < L/D < 95`, with the geometry and boundary-condition
mismatch acknowledged.

Tian 2024 buoyancy parameter thresholds are HITEC-specific but turbulent
horizontal cooling diagnostics, not a laminar TAMU switch. Chen 2021 and Yang
2024 are useful for nonuniform heating, vortex, and inclination classification,
not direct circular-pipe low-Re closures.

### Minor Losses And Fittings

The final litrev supports loss extraction discipline more strongly than it
supports transferable K values. Required fields for any admitted loss row:

- component or cluster ID;
- static, total, or reduced-static pressure basis;
- velocity and area basis;
- pressure/tap/CFD plane coordinates;
- hydrostatic and kinetic corrections;
- straight/developing loss subtraction;
- recovery length or recovery sensitivity;
- recirculation and redevelopment flags;
- same-QOI uncertainty.

Patino-Jaramillo 2022 is useful for planar low-Re tee logic and recirculation
maps, but its reduced-static planar coefficients are not circular-pipe TAMU
component K values. Salehi supports nonadditive close-coupled cluster logic, not
numerical HITEC losses. Al-Tameemi/Ricco is only relevant if a sharp miter
elbow geometry matches or as K(Re) sensitivity evidence.

### Heat Loss, Radiation, And Cooler Removal

The model must close energy before tuning internal Nu. Keep these paths
separate:

- heater electrical power versus heat actually delivered to salt;
- internal HTC;
- wall and insulation/contact conduction;
- passive external convection;
- radiation;
- quartz exposed-section losses;
- active jacket/cooler removal;
- storage;
- residual.

The litrev rejects one global UA as an exact closure. It supports a segmentwise
resistance network and explicit residual owner. Quartz emissivity/transmissivity
and OpenFOAM `rcExternalTemperature` provenance are still high-priority source
gaps.

### CFD-To-1D Reduction

CFD outputs should be produced in exactly the quantities the 1D model consumes:

- corrected static/total/reduced-static pressure changes;
- signed mass flow and section velocity measures;
- apparent section friction or cluster loss;
- wall heat rate, bulk temperature, effective `h`, `Nu`, `UA`, and external
  resistance;
- reverse-area/reverse-mass diagnostics;
- mesh/time uncertainty for the same QOI;
- plane-location and recovery sensitivity.

Do not label raw static pressure drop as irreversible loss. Do not call a
CFD-derived result a component K unless the planes isolate the component and
recovery is characterized.

## Branch-Level Consequences For Ethan

| Segment | Current consequence |
| --- | --- |
| Lower heated incline | Use developing/redeveloping heated inclined segment logic; do not convert pressure behavior into a global friction multiplier. |
| Lower corner clusters | Keep as section/cluster pressure evidence until basis, recovery, recirculation, and UQ gates pass. |
| Lower upcomer stainless span | Treat current Salt upcomer rows as topology diagnostics, not ordinary Nu/f/K fit rows. |
| Quartz test section | Model as smaller-bore exposed/radiative segment with separate quartz material and heat-loss treatment. |
| Upper upcomer stainless span | Candidate for recirculation-cell or signed-flow escalation only after onset/topology evidence. |
| Upper cooled incline / cooler | Prioritize cooler UA and segmented heat-removal calibration; do not lump into a global sink. |
| Upper corner clusters | Same section/cluster loss naming rule as lower corners. |
| Right-leg downcomer | Good future ordinary single-stream candidate, but current rows remain blocked by sign/enthalpy, interface recirculation, and same-QOI GCI gates. |
| Whole-loop predictive scorecard | Use mass flow only as a diagnostic consistency check; validate pressure, heat balance, wall/fluid temperatures, and topology simultaneously. |
| All branches | Carry nonblank property mode, source envelope, reset distance, and source-use status before fitting. |

## Negative Lessons From Current Ethan Evidence

The litrev explicitly imported negative model evidence as metadata:

- `64/Re` remains a reference/debug closure; it underpredicts de-buoyed fit-safe
  CFD friction in current comparisons.
- The F4 leg-class multiplier failed transfer and over-stiffened the loop.
- The F5 Ri-corrected friction form did not identify a robust buoyancy-friction
  correction because Ri/Re effects were not separable in the trial set.
- H1 aggregate fixed K is diagnostic evidence that losses matter, not an
  admitted localized closure.
- Pressure-increasing or negative corner residuals should not be clipped into
  positive K.
- Current internal Nu/HTC/UA rows are diagnostic until heat-loss, recirculation,
  wall-temperature, and same-QOI uncertainty gates pass.
- Current ordinary upcomer and downcomer Nu/f/K fits are blocked or diagnostic.
- TSWFC2, UMX1, and AMX1 variants are not admitted by current evidence.
- Global mass-flow match is rejected as a primary validation metric.

## Still-Blocking Inputs

The final unresolved claims table reduces the main implementation blockers to
eight TAMU-specific inputs:

1. Segmentwise nondimensional envelope: `Re`, `Pr`, `Gr`, `Gr*`, `Ri`, `Ra`,
   `Bo`, `Gz`, `L/D_h`, and reset distance for every case and segment.
2. Exact fitting geometry and cluster boundaries.
3. Reverse-flow and recirculation switching calibration.
4. Closure validation against TAMU data.
5. Pressure and velocity basis for extracted losses.
6. Final HITEC property package and salt state.
7. Heat-loss and power-partition calibration.
8. Boundary-condition equivalence by segment.

The remaining source gaps that matter most to modeling are heat capacity
provenance, low-Re circular fitting/transition data, OpenFOAM radiation
boundary provenance, same-QOI CFD uncertainty, and multi-QOI validation sources.

## Recommended Execution Order

1. Freeze the model interface: geometry, planes, pressure/velocity bases,
   reset distances, boundary-condition labels, and property mode.
2. Build the segmentwise nondimensional/source-envelope calculator.
3. Implement MF-01 with explicit pressure and energy residuals.
4. Add MF-02 section/cluster loss data structures and enforce component-K
   naming gates.
5. Close the segmentwise heat-loss and cooler/removal ledger before tuning Nu.
6. Validate against mass flow, segment pressure, heat balance, wall/fluid
   temperatures, topology, and same-QOI uncertainty on held-out cases.
7. Calibrate reverse-flow gates and only then activate MF-03 or MF-04 where
   topology requires them.
8. Keep transient and ROM forms parked until their source envelopes and FOM
   validation requirements are satisfied.

## Highest-Value Next Implementation Artifact

Build `case_segment_admission_engine` or equivalent with these inputs:

- segment geometry and orientation;
- source/property mode;
- boundary-condition class;
- pressure/tap/CFD planes and basis;
- wall/bulk temperatures and heat fluxes;
- signed mass flow and velocity fields when available;
- reset locations;
- source-envelope table;
- validation split metadata.

Expected outputs:

- nondimensional envelope table;
- source-overlap flags;
- allowed closure family per segment;
- rejected/diagnostic reasons;
- missing-input list;
- pressure and energy residual owners;
- topology state label;
- one machine-readable admission status per candidate closure.

That engine is the clean way to convert the litrev into executable model
selection logic without pretending unresolved TAMU inputs are already known.

## Guardrails

This report is a literature-to-modeling handoff. It does not edit or admit
model coefficients, native CFD outputs, solver state, registry rows, thesis
LaTeX, or source evidence. Any numerical closure promotion still requires the
source-envelope, property, pressure/energy accounting, topology, and same-QOI
uncertainty gates documented above.
