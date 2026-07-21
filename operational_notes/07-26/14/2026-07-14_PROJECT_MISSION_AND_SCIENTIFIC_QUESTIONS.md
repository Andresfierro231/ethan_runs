---
provenance:
  - reports/thesis_dossier/master_thesis_bullet_outline.md
  - reports/thesis_dossier/2026-07-14_thesis_presentation_update.md
  - .agent/BLOCKERS.md
  - .agent/STATE.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
tags: [mission, scientific-questions, coordination, blocker-driving, forward-model, closure-ledger, thesis-source]
related:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/master_thesis_bullet_outline.md
  - operational_notes/maps/README.md
  - .agent/BLOCKERS.md
  - .agent/STATE.md
task: AGENT-316
date: 2026-07-14
role: Coordinator/Writer
type: operational_note
status: complete
supersedes: []
superseded_by:
---
# Project Mission and Scientific Questions

## Mission

Build a defensible CFD-to-1D closure workflow for the TAMU molten-salt
natural-circulation loop.

The current high-fidelity reference is Ethan's OpenFOAM CFD. The goal is not to
tune one global coefficient until the 1D model matches CFD. The goal is to
reduce CFD into a provenance-controlled, branchwise closure ledger that tells us
which hydraulic, thermal, boundary, property, mesh, and admission terms are:

- predictive and allowed as setup-time model inputs;
- calibrated but validation-bounded;
- CFD-informed diagnostic evidence only;
- blocked by mesh, sign, heat-balance, recirculation, API, or model-form limits.

The finish-line model should predict loop mass flow and sensor/branch
temperatures from physical setup inputs without using CFD `mdot`, realized CFD
`wallHeatFlux`, or validation temperatures at runtime.

## Finish-Line Product

The project should produce:

- a 1D forward model with setup inputs in and `mdot`, pressure losses, branch
  temperatures, TP/TW sensor temperatures, and heat addition/removal out;
- a locked train/validation/holdout scorecard;
- a branchwise hydraulic closure ledger separating straight friction,
  development/reset, component loss, cluster loss, branch-apparent loss,
  buoyancy/kinetic terms, and residual;
- a thermal and heat-loss ledger separating internal convection, wall
  conduction, heater transfer, cooler/HX removal, passive loss, radiation
  metadata, wall/storage, and residual;
- a property-mode ledger so replication, updated-property, and sensitivity
  modes are not mixed during fitting;
- admission tables that say whether each row is fit-admissible,
  validation-only, diagnostic-only, or blocked;
- thesis-ready figures/tables with exact source paths and blocker status.

## Core Scientific Questions

1. Can a setup-only 1D model reproduce CFD loop mass flow without using CFD
   `mdot` as an input?
2. Can it reproduce branch and sensor temperatures without using realized CFD
   `wallHeatFlux` or validation temperatures as runtime inputs?
3. Which CFD-derived hydraulic closure terms are defensible as branchwise
   closures, and which are only section-effective or diagnostic?
4. Which thermal UA/HTC/Nu quantities survive mesh, sign, heat-balance, and
   downcomer-policy gates?
5. How do property choices change `Re`, `Pr`, `Gz`, buoyancy head, pressure
   residual, heat residual, and admission status?
6. Which boundary-condition submodels dominate prediction error: heater
   realized power, cooler/HX removal, wall-layer/external convection, radiation,
   or storage/residual?
7. Under what conditions does upcomer recirculation occur, and when does it
   invalidate single-stream `f_D`, `K`, or `Nu` labels?
8. Which CFD cases are steady, converged, correctly labeled, and admissible as
   training/validation/holdout evidence?
9. What uncertainty comes from mesh/GCI, time convergence, source envelopes,
   model form, sensor mapping, and unresolved APIs?
10. What thesis claims are supported now, and what must remain explicitly
    blocked or diagnostic?

## Current Gate State

Trust `.agent/BLOCKERS.md` for the current blocker list. As of this note, the
real open frontier is:

- closure-QOI mesh/GCI has zero publication-ready rows;
- thermal CFD-to-1D parity and internal-development models are unresolved;
- predictive heater/cooler/wall-layer submodels are unresolved;
- upcomer recirculation onset is extrapolated from sparse admitted data;
- Fluid lacks first-class external-boundary/wall-layer dictionaries;
- F6/Re-buoyancy friction correction is not validated.

Do not re-open superseded blockers: OF12 reconstruction failure, no mesh for
GCI, CFD-no-radiation parity, or refined reconstructed-`T` corruption. Those
have been resolved or superseded by narrower admission/model-form blockers.

## Agent Lanes

| Lane | Project responsibility | Gate-moving target |
| --- | --- | --- |
| `cfd-pp` | Postprocess fully converged CFD, categorize runs, label boundary conditions, harvest corrected Salt-Q, and expand admitted evidence. | Convert terminal CFD runs into correctly labeled, admissible training/validation/holdout rows. |
| `therm-reconstr` | Reconstructed `T`, mesh/GCI, thermal QOI triplets, and publication-readiness. | Move rows from repair-smoke/diagnostic to admitted, or explain exactly why they stay blocked. |
| `internal-Nu` | Thermal closure admission, sign/heat-balance review, internal HTC/Nu, and upcomer recirculation physics. | Decide which internal Nu/HTC rows are admissible and document recirculation onset conditions. |
| `hydraulics` | Pressure ledger, friction, reset/development, named/component losses, and mdot guardrails. | Turn H1/F6 ideas from proxy evidence into validation-safe hydraulic closures. |
| `forward-pred` | Predictive input contract, split discipline, scorecard, residual attribution, and end-to-end forward model. | Reopen forward-v1 only when hydraulic, thermal, boundary, sensor, and split gates are explicit. |
| `BC-modeling` | Heater, cooler/HX, wall-layer, external convection/radiation semantics, and Fluid API handoff. | Replace imposed CFD cooler/heater evidence with setup-only predictive boundary models. |
| `thesis-pres-docs` | Human-facing synthesis, thesis dossier, weekly presentation story, and blocker hygiene. | Keep claims current, defensible, and free of stale blockers or overclaims. |
| `dmdc` | Separate TAMU data/DMDc support lane. | Support validation/catalog/dashboard needs without distracting from CFD-to-1D closure gates. |

## How The Coordinator Should Drive Progress

Prompt agents toward decisions that change gate state, not toward more broad
inventory. A useful agent result should do at least one of these:

- resolve, supersede, or narrow a blocker;
- promote a row from diagnostic to validation-only or fit-admissible;
- demote a tempting but unsafe claim to diagnostic-only with evidence;
- convert a proxy model into a faithful implementation;
- harvest a live/completed CFD run into admission-labeled evidence;
- update the forward scorecard under the locked split without violating input
  discipline;
- produce thesis-ready wording that is more accurate than the previous story.

Avoid work that only adds new tables without changing admission, prediction, or
uncertainty status.

## Immediate Priorities

1. `cfd-pp`: postprocess fully converged runs and corrected Salt-Q when
   terminal; produce a case/run admission inventory with BC labels and split
   eligibility.
2. `internal-Nu`: document upcomer recirculation onset conditions and connect
   them to coefficient-naming rules.
3. `hydraulics`: decide whether H1 can become a faithful localized closure, and
   whether F6/Re correction deserves the next bounded run.
4. `BC-modeling`: turn heater/cooler/wall-layer decision tables into the next
   executable setup-only boundary model.
5. `forward-pred`: keep final forward-v1 blocked until the above gates land,
   then rebuild the scorecard.
6. `thesis-pres-docs`: keep the mission, questions, blocker state, and next
   meeting story synchronized.

