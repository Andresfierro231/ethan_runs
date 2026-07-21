---
task: AGENT-472
date: 2026-07-16
role: Coordinator/Writer
type: operational_note
status: complete
tags: [forward-predictive-model, fluid-walls, steady-state, thermal-circuit, boundary-layer, upcomer-onset]
related:
  - .agent/BOARD.md
  - reference/geometry_reference.md
  - operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
---
# Steady-State `fluid+walls` 1D Model Form

## Purpose

This note records the updated final 1D model-form vision after the July 16 user
coordination discussion. The current target is steady state only. Do not include
wall storage, transient terms, or time-dependent heat capacity in the present
model form.

The model-form name to carry forward is:

```text
fluid+walls
```

The name is meant to make the modeling contract explicit: the 1D state is not
just a fluid energy balance with fitted heat leaks. Each segment has a fluid
bulk state, a wall/material stack, external boundary conditions, pressure terms,
source/sink role, validity flags, and uncertainty/admission status.

## Segment Ledger Contract

Every segment or branch-region should carry these fields:

| Field | Current status | Notes |
| --- | --- | --- |
| Geometry | Mostly available | `reference/geometry_reference.md` is authoritative. The physical upcomer is `left_lower_leg -> test_section_span -> left_upper_leg`; the test section is the middle upcomer span. |
| Material stack | Partially available | Steel/insulation/quartz distinctions are known in geometry and boundary packages, but they need one `fluid+walls` readiness ledger. |
| Pressure model | Partially available | Pressure ledgers and pressure maps exist; final coefficient admission remains blocked in recirculating or non-GCI rows. |
| Thermal circuit | Partially available | CFD setup values and heat ledgers exist; a segment-local resistance/UA implementation contract is still needed. |
| Source/sink role | Available but needs final ledger | Heater, cooler/HX, passive ambient wall, test section, and junction roles exist in prior ledgers; they need assembly under the `fluid+walls` model form. |
| Boundary-layer/development state | Diagnostic/planned | LitRev supports reset/development/Graetz treatment. Needs scorecard and CFD-informed branch flags. |
| Recirculation/admission flags | Available for many rows | Upcomer recirculation evidence and branch masks exist; ordinary single-stream coefficient fitting remains rejected for current upcomer rows. |
| Uncertainty status | Partial | Time-window UQ is strong; closure-QOI mesh/GCI remains a live blocker for publication-grade coefficients. |

Conclusion: we do not yet have everything in one admitted model-ready package.
We have enough evidence to define the model form, and enough partial inputs to
build a readiness ledger and first scorecards. The next coordination artifact is
`TODO-PREDICT-FLUID-WALLS-READINESS-LEDGER`.

## Steady Energy Balance

For a segment `i` with length coordinate `s`, the steady fluid energy balance is:

```text
d/ds[ mdot cp(T) T ] =
    q'_heater_to_fluid,i
  - q'_cooler_removed,i
  - q'_wall_loss,i
  + q'_other_source_to_fluid,i
```

No storage term belongs in this current model.

The sign convention should be:

- positive `q'` adds heat to the fluid;
- negative `q'` removes heat from the fluid;
- each term must keep its physical owner, so internal convection does not absorb
  heater, cooler, passive wall, radiation, or junction residuals.

## Thermal Circuit Path

For ordinary pipe or wall-covered regions, the segment heat exchange should be
computed through a resistance path:

```text
fluid bulk
  -> internal convection / thermal boundary layer
  -> pipe wall conduction
  -> insulation or local material layer
  -> external convection to ambient
  -> external radiation to surroundings
```

In resistance form per unit length:

```text
R'_total =
    R'_internal_convection
  + R'_wall_conduction
  + R'_insulation_or_layer_conduction
  + R'_external_convection_radiation

q'_wall_loss = (T_bulk - T_external_drive) / R'_total
```

where an initial implementation can use:

```text
R'_internal_convection = 1 / (h_i P_i)
R'_wall_conduction = ln(r_wall_outer / r_wall_inner) / (2 pi k_wall)
R'_insulation_conduction = ln(r_ins_outer / r_wall_outer) / (2 pi k_ins)
R'_external_convection_radiation = 1 / ((h_ext + h_rad) P_outer)
```

and a linearized radiation coefficient:

```text
h_rad = emissivity * sigma * (T_surface + T_sur) * (T_surface^2 + T_sur^2)
```

The exact drive temperature must be a declared model choice:

- bulk-fluid drive;
- inner-wall drive;
- pipe outer-wall drive;
- insulation outer-surface drive.

The preferred predictive runtime inputs are setup quantities: geometry,
materials, `h`, `Ta`, `Tsur`, emissivity, layer thicknesses, and calibrated
parameters frozen from training rows. Realized CFD `wallHeatFlux` is diagnostic
or scoring evidence only.

## Test Section Equation

The test section is not deleted. It is modeled as a bare-quartz, electrically
heated, externally losing segment inside the upcomer path.

Use this steady-state form:

```text
q'_test_section_to_fluid =
    q'_electrical_deposition_to_fluid_or_wall
  - q'_quartz_to_ambient_loss
```

Expanded:

```text
q'_quartz_to_ambient_loss =
  (T_drive - T_external_drive) / R'_quartz_external
```

So:

```text
q'_test_section_to_fluid =
    q'_electrical_deposition_to_fluid_or_wall
  - (T_drive - T_external_drive) / R'_quartz_external
```

This can be positive or negative. If electrical deposition exceeds external
quartz losses, the segment heats the fluid. If bare-quartz external loss exceeds
electrical deposition, the segment is a net sink. Existing mainline evidence
suggests the latter can occur, but the model should compute the sign rather than
hard-code it.

For the test section:

- material stack is fused quartz, not insulated steel pipe;
- bore is smaller than the other main pipe spans;
- it is physically `test_section_span`, the middle span of the upcomer;
- it participates in buoyancy and recirculation, so it cannot be removed from
  the loop model even when a diagnostic ablation improves a temperature RMSE.

## Boundary-Layer And Junction Plan

The boundary-layer and junction treatment should be staged, because current CFD
and LitRev evidence support the model architecture better than final fitted
coefficients.

1. **Define branch-local thermal entrance state.**
   Use reset points after bends, expansions, contractions, heater/cooler source
   changes, and junctions. Carry local `x/D`, `L/D`, Graetz number `Gz`, and
   thermal boundary condition class.

2. **Use baseline internal convection first.**
   For ordinary non-recirculating branches, start with literature/default
   laminar/developing convection. Do not fit one global Nu. Treat branch-specific
   internal convection as a model slot with admission flags.

3. **Score boundary-layer toggles by segment.**
   The boundary-layer scorecard should test:
   - hydraulic entrance/reset terms, including Shah/developing apparent friction;
   - thermal entrance/Graetz terms;
   - wall-adjacent versus bulk drive;
   - wall/layer resistance;
   - branch-specific inclusion/exclusion masks.

4. **Treat junctions/stubs/connectors separately.**
   Junction heat loss and mixing should not be hidden inside pipe Nu. Use a
   junction/stub/connector thermal region with:
   - aggregate surface-area or patch-role heat-loss evidence;
   - named residual/mixing term when a physical bracket is missing;
   - diagnostic-only status until inlet/outlet enthalpy and surface ownership
     are sufficient.

5. **Keep upcomer out of ordinary single-stream fitting.**
   Current upcomer evidence supports recirculation/onset or section-effective
   diagnostics. The upcomer needs a throughflow-pipe plus recirculation-cell
   model, not an ordinary single-stream `Nu`, `f_D`, or `K`.

## Upcomer Onset CFD Study Needed

Existing evidence shows recirculation, but does not calibrate onset. A systematic
CFD anchor plan should include:

1. **High-Re / high-insulation cell-off target.**
   Push loop Re toward or above the current hand-estimate band near a few
   hundred, while reducing wall-core thermal drive as much as physically
   plausible. This is intended to observe transition to low or zero reverse
   flow.

2. **Low-Q / low-insulation cell-max target.**
   Use weak loop forced flow and strong wall-core thermal drive to estimate
   saturation or maximum recirculation strength.

3. **Small Q x insulation matrix.**
   Use a representative Salt case, likely the mid operating point, with a small
   matrix such as 3 Q levels by 3 insulation levels. The goal is to decouple Re
   from local wall-core Delta T instead of moving only along one natural-
   circulation curve.

4. **Optional forced-flow feasibility study.**
   If solver setup permits, a forced-flow or pump-like case would sweep Re at
   nearly fixed thermal drive and provide the cleanest onset map. This should be
   treated as a feasibility lane, not assumed available.

Every onset case should emit or enable:

- `U`, `T`, `wallHeatFlux`;
- `Re`, `Pr`, `Ri`, `Gr`, `Ra`, `Gz`;
- wall-core Delta T;
- reverse area fraction;
- reverse mass fraction;
- secondary velocity or in-plane circulation metric;
- time-window steady-state status;
- mesh/time uncertainty status.

AGENT-471 is already staging a high-heat no-recirculation probe. That is useful
as one anchor attempt, but it should not replace the systematic matrix.

## Board Rows Added By This Coordination Pass

- `TODO-PREDICT-FLUID-WALLS-READINESS-LEDGER`
- `TODO-UPCOMER-ONSET-CFD-ANCHOR-MATRIX`
- `TODO-PAPER-FINAL-1D-MODEL-FORM-DOCS`

Existing rows that remain part of the same plan:

- `TODO-PREDICT-WALL-THERMAL-CIRCUIT`
- `TODO-PREDICT-TEST-SECTION-HEAT-LOSS`
- `TODO-PREDICT-BOUNDARY-LAYER-DEVELOPMENT-SCORECARD`
- `TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL`
- `TODO-PREDICT-SEGMENT-THERMAL-MODELS`
- `TODO-PREDICT-SEGMENT-PRESSURE-MODELS`
- `TODO-PREDICT-COUPLED-SEGMENT-M3TS-SCORECARD`

