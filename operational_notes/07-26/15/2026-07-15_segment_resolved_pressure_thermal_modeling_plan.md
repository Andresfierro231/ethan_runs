---
provenance:
  - .agent/BOARD.md
  - operational_notes/maps/forward-predictive-model.md
  - reports/thesis_dossier/2026-07-15_integrated_weekly_powerpoint_outline_definitions_first.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/report.md
  - work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan/README.md
tags: [forward-predictive-model, pressure-balance, thermal-balance, segment-models, m3ts]
related:
  - operational_notes/07-26/15/2026-07-15_m3_successor_test_section_heat_loss_requirement.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-431
date: 2026-07-15
role: Coordinator/Writer
type: operational_note
status: complete
---
# Segment-Resolved Pressure/Thermal Modeling Plan

## Correction To The Compact Equation

The presentation shorthand

```text
sum(dp_drive(mdot) - dp_loss(mdot; f_D, K)) = 0
```

is too compressed for implementation. It is acceptable only as a high-level
root-solve label after the thermal state has already been solved.

The expanded model must treat buoyancy drive as a function of temperature,
density, elevation, and loop position:

```text
Delta p_drive =
  integral_loop rho(T(s), p(s), composition, property_lane) g dz(s)
```

For a closed loop with uniform density this cancels. Natural-circulation drive
appears because heater/upcomer and cooler/downcomer legs have different
temperature and density fields at different elevations. `mdot` still matters,
but indirectly: changing `mdot` changes residence time, heat pickup/removal,
`T(s)`, density, and therefore the buoyancy integral.

Pressure loss is also segment-local:

```text
Delta p_loss =
  sum_i [
    f_i(Re_i, Pr_i, Ri_i, regime_i, roughness_i, geometry_i) (L_i/D_i) q_i
    + K_i(local_geometry_i, reset_i, development_i, regime_i) q_i
  ]
```

where `q_i = 0.5 rho_i V_i^2` and each segment can have a different model form.

## Required Modeling Policy

Future agents should not force one global pressure or thermal closure across the
whole loop. Different model forms are expected in:

- heater / heated incline;
- test section / upcomer;
- cooler / HX / cooling branch;
- downcomer;
- lower and upper horizontal legs;
- junctions, stubs, connectors, reducers, and mixing regions.

The pressure and thermal balances are coupled:

```text
mdot -> segment residence time -> T_i(s) -> rho_i, mu_i, cp_i, k_i
     -> buoyancy drive and pressure losses -> new mdot
```

The solver target is a coupled fixed point/root, not an isolated scalar
friction fit.

## Segment Model Slots

Each region should declare its own candidate model slots.

Pressure slots:

- buoyancy/elevation contribution using local density and `dz`;
- distributed friction for straight or nearly straight sections;
- reset/development loss after bends, expansions, contractions, or thermal
  redevelopment;
- localized component `K` where a component can be physically bracketed;
- branch/junction apparent loss where mixing or recirculation prevents a true
  component `K`;
- recirculation/onset diagnostic label where single-stream `f_D`/`K` is invalid.

Thermal slots:

- heater fluid-entry model, e.g. `Q_heater = eta_heater P_electrical` or a
  resistance/storage model;
- cooler/HX removal model, e.g. `UA DeltaT`, epsilon-NTU, or an admitted setup
  boundary form;
- test-section distributed heat-loss model (`M3+TS` requirement);
- passive external boundary loss with h/Ta/Tsur/emissivity/coverage;
- wall/layer resistance and storage where admitted;
- radiation only if represented without double counting CFD `wallHeatFlux`;
- junction/stub/connector heat loss and mixing residuals as separate terms.

## Admission Guardrails

- Do not use realized CFD `wallHeatFlux`, CFD mdot, imposed CFD cooler duty, or
  validation temperatures as predictive runtime inputs.
- Do not fit true `Nu`, `f_D`, or `K` from recirculating rows.
- Do not let internal Nu absorb heater, cooler, passive loss, wall storage, or
  radiation residuals.
- Preserve train/validation/holdout split and report fit versus score rows.
- Label section-effective diagnostics separately from true closure coefficients.

## Board Plan

The next staged tasks are now on `.agent/BOARD.md`:

1. `TODO-PREDICT-SEGMENT-EQUATION-CONTRACT`
2. `TODO-PREDICT-SEGMENT-PRESSURE-MODELS`
3. `TODO-PREDICT-SEGMENT-THERMAL-MODELS`
4. `TODO-PREDICT-COUPLED-SEGMENT-M3TS-SCORECARD`

This order is intentional: freeze the equation/model-slot contract before
building pressure and thermal scorecards, then run the coupled setup-only M3+TS
candidate.
