# Research Plan: End-To-End Predictive 1D Model

Task: `AGENT-286`
Date: 2026-07-13

## Scientific Goal

Build a 1D model that predicts mass flow rate and sensor temperatures from
physical setup inputs without requiring CFD mdot, CFD realized wall flux, or
CFD target temperatures as runtime inputs.

The desired predictive hierarchy is:

```text
heater/cooler/setup inputs
  -> coupled thermo-hydraulic solve
  -> mdot
  -> bulk and wall temperature state
  -> section heat gains/losses
  -> TP/TW sensor predictions
```

## Model Modes To Keep Separate

### Mode A: Diagnostic Fixed-mdot Parity

Uses CFD mdot and may use CFD realized wall flux. This is useful for isolating
where physics terms disagree. It is not predictive.

Existing packages: AGENT-270, AGENT-271, AGENT-279.

### Mode B: Forward With Imposed Cooler Duty

Uses physical geometry/properties, heater input, and a declared cooler duty.
Solves mdot and temperature state. This is predictive for mdot and temperatures
conditional on cooler duty.

This is the best next implementation target because it removes the first-order
HX uncertainty while forcing the model to predict pressure-rooted mdot.

### Mode C: Fully Predictive HX

Uses heater input and cooler/HX operating conditions, not imposed cooler duty.
Solves cooler duty through UA or epsilon-NTU and predicts mdot plus sensors.

This is the final target for thesis-strength predictive heat loss.

## Phase 1: Input Contract And Runtime Hygiene

Goal: prove the forward model is not accidentally reading validation targets.

Tasks:

1. Create a strict input contract for the forward model.
2. Mark every field as one of:
   - setup input,
   - calibrated parameter,
   - validation target,
   - diagnostic CFD evidence,
   - uncertainty metadata.
3. Add tests or assertions that predictive modes do not consume:
   - CFD mdot,
   - realized CFD wallHeatFlux,
   - CFD target Tmean/TP/TW,
   - fitted parameters from held-out rows.

Acceptance criteria:

- A single config/table can be reviewed before a run.
- Output metadata declares which predictive mode was used.
- Validation targets are joined only after model outputs are generated.

Primary task: `TODO-PRED-INPUT-CONTRACT`.

## Phase 2: Forward-v0 With Imposed Cooler Duty

Goal: solve mdot and sensor temperatures with cooler duty supplied as a boundary
condition.

Runtime inputs:

- geometry,
- properties,
- heater input,
- imposed cooler duty,
- ambient/Ta and wall/insulation setup,
- hydraulic closure,
- heater/test-section contract,
- external heat-loss model.

Do not use:

- CFD mdot,
- CFD realized wallHeatFlux,
- CFD sensor temperatures as anchors.

Acceptance criteria:

- mdot is solved from buoyancy equals losses,
- temperature periodicity is solved,
- TP/TW predictions are emitted,
- mdot and sensor comparisons are validation-only,
- residuals are split into hydraulic, cooler, heater/test, external, and sensor
  lanes.

Primary task: `TODO-PRED-FORWARD-V0`.

## Phase 3: Source And Boundary Corrections

Goal: correct the biggest non-HX thermal contract gaps using low-dimensional
parameters.

### Heater

Current evidence shows realized heater wall flux is about 0.918 of imposed
heater power across Salt2-4. Do not hard-code per-case heater values. Test:

```text
Q_heater_to_fluid = eta_heater_global * Q_heater_input
```

Acceptance criteria:

- one global or family-level parameter,
- no case-specific heater hacks,
- section heat residual improves or blocker remains documented.

### Test Section

The test section should not remain a pure +37 W source if CFD realized wall flux
is a net sink. Test:

```text
Q_test_net = Q_test_input - hA_test * (T_drive_test - Ta_test)
```

Acceptance criteria:

- test-section residual is reported separately,
- source and loss parts remain visible,
- no passive external loss is hidden in the heater parameter.

Primary task: `TODO-PRED-HEATER-TEST-CONTRACT`.

## Phase 4: External Wall-Layer Mapping

Goal: make the external wall boundary use a temperature comparable to the CFD
wall-boundary driving state.

The CFD boundary condition acts at the patch/wall state, not at the 1D segment
bulk temperature. The current N2 replay is therefore a bulk-temperature stress
test, not a CFD-equivalent wall boundary.

Test these candidates:

```text
E0_bulk:
q_ext = hA * (T_path_bulk - Ta)

E1_wall_shell:
q_ext = hA * (T_wall_shell - Ta)

E2_blend:
T_drive = T_path_bulk + beta_family * (T_wall_shell - T_path_bulk)
q_ext = hA * (T_drive - Ta)
```

Acceptance criteria:

- section-family parameters only,
- no per-case hA hacks,
- cooler/HX lane remains separate,
- radiation policy remains explicit,
- rows with recirculation or poor support are diagnostic-only.

Primary task: `TODO-PRED-WALL-LAYER`.

## Phase 5: Predictive HX

Goal: replace imposed cooler duty with a predictive cooler/HX model.

Candidate forms:

```text
Q_cooler = UA_HX * DeltaT_lm
```

or:

```text
Q_cooler = epsilon(mdot, UA, C_min, C_max) * C_min * (T_hot_in - T_cold_in)
```

Acceptance criteria:

- one low-dimensional HX parameterization,
- trained on a declared subset,
- held-out rows scored without refit,
- cooler residual reported separately from ambient wall loss.

Primary task: `TODO-PRED-HX-FIT`.

## Phase 6: Hydraulic Gate

Goal: make sure predicted mdot is credible before claiming thermal predictivity.

Use pressure-only fit-safe rows first. The model must report:

- buoyancy head,
- distributed losses,
- named/lumped minor losses,
- residual pressure,
- mdot error,
- fit-safe flags by section.

Acceptance criteria:

- no fixed-mdot scoring in predictive mode,
- pressure-root convergence documented,
- bad pressure spans do not silently tune thermal parameters.

Primary task: `TODO-PRED-HYDRAULIC-GATE`.

## Phase 7: Thermal Mesh, Time, And Heldout Validation

Goal: move from plausible engineering model to defensible research model.

Required gates:

- late-window uncertainty for fitted/scored rows,
- mesh uncertainty for thermal QOIs,
- corrected-Q/low-heat rows admitted only after terminal/latest-time review,
- train/validation split locked before fitting,
- no parameter added unless it improves held-out residuals.

Acceptance criteria:

- every fitted parameter has training rows and validation rows,
- uncertainty is visible in score tables,
- blocked rows remain blocked rather than quietly excluded.

Primary tasks:

- `TODO-PRED-THERMAL-MESH-GATE`
- `TODO-PRED-VALIDATION-SPLIT`
- `TODO-PRED-ENDTOEND-SCORE`

## Suggested Immediate Sequence

1. `TODO-PRED-INPUT-CONTRACT`
2. `TODO-PRED-FORWARD-V0`
3. `TODO-PRED-HEATER-TEST-CONTRACT`
4. `TODO-PRED-WALL-LAYER`
5. `TODO-PRED-HX-FIT`
6. `TODO-PRED-HYDRAULIC-GATE`
7. `TODO-PRED-VALIDATION-SPLIT`
8. `TODO-PRED-ENDTOEND-SCORE`

The reason to run the imposed-cooler forward-v0 before predictive HX is simple:
cooler/HX mismatch is the largest thermal-state lever. Supplying cooler duty
temporarily lets the team debug mdot, heater/test-section, wall-layer, and
sensor behavior without conflating every error with HX under-removal.

Existing board rows `TODO-PREDICT-HEATER-FLUID-FRACTION` and
`TODO-PREDICT-COOLER-REMOVAL` should be treated as narrower predecessors of
`TODO-PRED-HEATER-TEST-CONTRACT` and `TODO-PRED-HX-FIT`, respectively. Keep
their evidence, but run the new sequence so the end-to-end prediction contract,
heldout split, and validation-only target hygiene are enforced.

## Definition Of Done For Predictive Claim

The model can be called predictive for a stated operating envelope only when:

- mdot is solved, not supplied,
- heater/cooler/test-section inputs are physical setup or calibrated parameters,
- no realized CFD wall flux is a runtime input,
- no validation temperatures anchor the solution,
- held-out cases are scored,
- uncertainty bars include time-window and mesh readiness,
- residuals are decomposed by hydraulic, HX, heater/test, external wall, and
  sensor lanes,
- all blocked rows remain visible.
