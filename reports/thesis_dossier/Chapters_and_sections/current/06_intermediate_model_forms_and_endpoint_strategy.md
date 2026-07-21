---
provenance:
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
  - work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/README.md
tags: [thesis-section, current-section, endpoint-strategy, model-form-bakeoff, numerical-methods, sam]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
task: AGENT-510
date: 2026-07-17
role: Writer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Intermediate Model Forms And Endpoint Strategy

## Purpose

The preferred endpoint is a fully admitted final predictive 1D model. That model
must predict mass flow, branch temperatures, and TP/TW sensor temperatures from
setup inputs only, using coefficients trained only on the canonical training
rows and then frozen before holdout or external scoring.

The thesis also needs a rigorous fallback if every final gate does not close in
time. The defensible endpoint is then a scored model-form ladder: each step must
state its assumptions, required CFD postprocessing, training cost, runtime cost,
admission status, and failure modes. This keeps the work explainable and lets
the thesis compare progressively richer physics without pretending that a
diagnostic replay is a final predictive model.

## Locked Split Policy

All endpoint comparisons use the canonical final predictive split.

| Role | Rows | Allowed use |
| --- | --- | --- |
| Final training | `salt1_nominal`, `salt2_jin_nominal`, `salt3_jin_nominal`, `salt4_nominal` | Fit admitted final model terms. |
| Training support | `salt1_lo10q`, `salt1_hi10q`, `salt4_lo5q`, `salt4_hi5q` | Support trend and sensitivity checks with labels preserved. |
| Holdout/testing | `salt2_lo5q`, `salt2_hi5q` | Score a frozen model only. |
| External test | `val_salt2` | Blind external-style score after the model is frozen. |
| Future holdout | Salt2/Salt4 +/-10Q and new CFD rows | Score only after terminal harvest and row-specific admission. |

No endpoint table may use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD
cooler duty, pressure loss from the scored row, or validation TP/TW temperatures
as runtime inputs for a predictive claim.

## Model-Form Ladder To Score

| Form | Thesis role | Runtime inputs | Required postprocessing | Cost | Admission status to report |
| --- | --- | --- | --- | --- | --- |
| M0 setup-only baseline | Lower bound and sanity check. | Geometry, properties, setup heater/cooler assumptions, ambient inputs. | Minimal case metadata and sensor targets. | Low training cost; low runtime cost. | Predictive if no forbidden runtime inputs enter, but expected to have large residuals. |
| M1 CFD thermal-boundary replay | Diagnostic upper-context for heat placement. | Setup plus realized CFD thermal ledgers. | Patch heat ledger, wall heat flux, section heat balance. | Moderate postprocessing; low runtime solve cost. | Diagnostic only because realized CFD heat is a scored-row output. |
| M2 admitted heater+cooler boundary model | First credible boundary-submodel predictive candidate. | Setup heater power, setup cooler/HX inputs, ambient/radiation inputs, admitted heater/cooler coefficients. | Split-aware heater/cooler admission tables and runtime-input audit. | Moderate training; low runtime. | Predictive only for admitted terms; passive wall/test-section may remain blocked. |
| M3 segment-only `fluid+walls` | Main reduced-order network without explicit junction ownership. | Segment geometry, pressure slots, thermal circuits, source/sink roles, admitted coefficients. | Segment pressure rows, heat ledger rows, sensor targets, runtime audit. | Moderate to high training; moderate runtime nonlinear solve. | Useful comparison even if not fully admitted, provided diagnostic rows are labeled. |
| M4 junction-aware `fluid+walls` | Tests whether structured junction/stub heat and pressure ownership improves residual attribution. | M3 inputs plus junction buckets, branch-apparent losses, and junction thermal roles. | Junction/stub heat split, corner/branch pressure ledgers, plane-placement admission. | High postprocessing; moderate runtime. | Current junction evidence is thesis-useful but pressure K remains diagnostic until admitted. |
| M5 hybrid upcomer model | Separates throughflow pipe path from recirculation-cell exchange path. | M3/M4 inputs plus recirculation flags, onset anchors, exchange terms if admitted. | Upcomer PM5/PM10 diagnostics, onset matrix, low-recirculation anchors. | High research cost; moderate runtime if parametrized. | Ordinary single-stream `Nu`, `f_D`, and `K` rows remain invalid in recirculation-dominated upcomer states. |
| M6 frozen final predictive candidate | Desired endpoint. | Setup inputs and coefficients trained only on final training rows. | Complete train/support/holdout/external scorecard and assumption ledger. | Highest training and QA cost; low to moderate runtime. | Fully admitted only if hydraulic, thermal, sensor, recirculation, and runtime-leakage gates pass. |

The thesis should not rank these only by scalar RMSE. Each scorecard should show
mass-flow error, pressure residual movement, branch heat residuals, TP/TW sensor
errors, loop temperature-difference error, runtime-input violations, model
complexity, and uncertainty/admission state.

## Implemented M0-M4 Bakeoff Package

The current implementation package is:

```text
work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/
```

It converts the M0-M4 portion of this ladder into thesis-ready tables:
`model_form_contracts.csv`, `model_form_scores.csv`,
`model_form_costs.csv`, and `model_form_failure_modes.csv`. The package keeps
the locked split intact and reports final-score gaps explicitly:

- `M0` is represented as a setup-only predictive baseline shell with
  `prediction_missing` numeric scores.
- `M1` carries legacy diagnostic replay scores only; it is not predictive.
- `M2` carries admitted heater/cooler boundary residual evidence, but full
  model scoring is blocked by wall/test-section physics.
- `M3` carries legacy segment-network score context but remains blocked for
  final locked-split scoring because `FINAL_FREEZE_TBD` does not exist.
- `M4` carries junction-aware attribution evidence; pressure corner-K and
  junction coefficients remain diagnostic with zero fit-admitted rows.

The package is the current table source for thesis claims about intermediate
model forms. It does not supersede the need for a final frozen predictive
candidate; it documents what can be claimed while M5/M6 remain blocked.

## Cost And Input Comparison Table

Every final or appendix model-form table should include:

- equations or residual statements solved by the form;
- setup/runtime inputs allowed at prediction time;
- row families used for training, support, holdout, and external scoring;
- CFD products needed before the form can be scored;
- whether the form requires OpenFOAM resampling, section ledgers, patch ledgers,
  pressure ladders, or only existing extracted tables;
- computational training cost, including Fluid sweeps, nonlinear solves, and
  any compute-node postprocessing;
- operational runtime cost once coefficients are frozen;
- known caveats and expected failure modes;
- admission status: admitted, diagnostic, blocked, or future-work.

## Numerical Algorithms Section

The thesis should include a numerical-methods section even though the model is a
reduced-order 1D network rather than a full CFD solver. It should describe:

- unknowns: loop mass flow, branch/segment fluid temperatures, wall/interface
  temperatures where modeled, pressure drops, and optional exchange variables;
- residual equations: loop pressure closure, segment steady energy balances,
  wall thermal-circuit balances, heater/cooler source terms, and sensor
  projection equations;
- property updates: density, viscosity, `cp`, conductivity, `Re`, `Pr`, `Ri`,
  `Gz`, and buoyancy head updated from the current temperature estimate;
- coupling strategy: pressure and thermal solves are coupled because mass flow
  changes heat advection and temperature changes buoyancy and friction;
- nonlinear solve method: bracketing/root solve or Newton-like iteration,
  convergence tolerances, accepted-root flags, finite-output checks, and
  failure modes;
- scorecard generation: freeze candidate coefficients, run training/support
  rows, then run holdout/external rows without fitting or model selection.

The distinction from other numerical methods should be explicit:

- OpenFOAM finite volume CFD solves local conservation equations over 3D cells;
  our model solves a reduced set of 1D control-volume balances over named
  branches and components.
- FEM is usually framed around basis functions and weak-form residuals over
  elements; our thesis model is a network/control-volume balance with empirical
  or literature closure laws.
- Systems codes such as SAM also solve reduced-order network balances, but this
  thesis contribution is the CFD-to-1D closure and admission workflow for this
  loop, not a direct SAM validation study.

## SAM-Facing Interpretation

The SAM-facing thesis section should state how these results can be useful to
ANL SAM without overstating the claim:

- branchwise friction, reset, and junction-apparent loss ledgers identify where
  a systems-code component library may need component-specific closures instead
  of a global multiplier;
- `fluid+walls` thermal circuits provide a structured way to separate internal
  convection, wall conduction, insulation, external convection, radiation,
  heater transfer, cooler removal, and residual heat loss;
- upcomer recirculation flags identify states where a single throughflow pipe
  closure should not be trusted without an exchange or mixing model;
- the admission ledger gives SAM users a disciplined way to carry uncertainty,
  split role, and validity flags with each coefficient;
- the thesis does not validate SAM against experiment unless independent
  experimental comparisons are added later.

## Near-Term Execution Strategy

The next week should prioritize maximum thesis value per unit effort:

1. Keep the final predictive scorecard shell moving, but freeze candidates only
   when their runtime-input audits and admission gates pass.
2. Score M0-M4 even if M5/M6 remain blocked; those comparisons are explainable
   and appendix-worthy.
3. Use M4 junction-aware comparisons as a thesis contribution even before
   pressure corner-K is fit-admitted, provided diagnostic status is clear.
4. Treat the upcomer as a separate hybrid/onset lane; do not force ordinary
   `Nu`, `f_D`, or `K` fits through recirculating rows.
5. Use future +/-10Q and new CFD only after terminal/admission packages; do not
   weaken the locked split to get more apparent validation rows.
