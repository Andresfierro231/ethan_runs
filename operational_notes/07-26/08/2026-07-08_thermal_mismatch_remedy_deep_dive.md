# 1D Thermal-State Mismatch Remedy Deep Dive

Date: `2026-07-08`
Task: `AGENT-209`
Role: Coordinator / Implementer / Writer

## Scope

This note answers four follow-up questions:

1. Exact heater imposed duty and heater wallHeatFlux input.
2. Why the 1D state remains hotter, whether pipe walls/cooler are modeled
   correctly, and four remedy paths tried against existing artifacts.
3. What to do about the missing `qr` radiation term.
4. How to add an explicit fixed-mdot / frozen-hydraulics Fluid mode with
   scientific transparency.

Generated package:

- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/`
- Builder: `tools/analyze/build_thermal_mismatch_remedy_deep_dive.py`
- Tests: `tools/analyze/test_thermal_mismatch_remedy_deep_dive.py`

Inputs:

- `work_products/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv`
- `work_products/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv`
- Fluid solver source, read-only:
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`

## Exact Heater Values

From `heater_values.csv`:

| Case | Heater imposed duty W | Heater wallHeatFlux input W | Imposed minus wallHeatFlux W |
| --- | ---: | ---: | ---: |
| Salt 2 | 265.700 | 243.519 | 22.181 |
| Salt 3 | 297.500 | 273.155 | 24.345 |
| Salt 4 | 337.600 | 310.487 | 27.113 |

The wallHeatFlux input is the OpenFOAM interface heat to the fluid on the heater
patch group.  The imposed duty is the boundary-control value.  The difference is
not a fitting knob; it is a boundary/solid/storage/staging caveat until a
same-time solid-energy audit is available.

## Why the 1D State Is Still Hotter

Observed fixed-mdot baseline:

| Case | CFD Tmean K | Fixed-mdot current 1D Tmean K | Error K | Current 1D qhx W | CFD cooler loss W |
| --- | ---: | ---: | ---: | ---: | ---: |
| Salt 2 | 450.3 | 512.526 | +62.226 | 46.292 | 136.351 |
| Salt 3 | 463.7 | 527.686 | +63.986 | 49.663 | 150.770 |
| Salt 4 | 479.2 | 544.226 | +65.026 | 53.472 | 169.227 |

The first-order issue is the cooling jacket/HX path.  The current Fluid
predictive air-side model removes only 46-54 W while the CFD cooler patch group
removes 136-169 W.  This under-removal is large enough to explain most of the
mean-temperature error.

The source-side mismatch is also real but secondary:

- Heater imposed duty is 22-27 W above heater wallHeatFlux.
- The 1D Salt cases add `37 W` as a test-section source.
- CFD test-section wallHeatFlux is instead a net sink of 5.680, 10.545, and
  16.769 W for Salt 2/3/4.

Combined known first-order correction magnitudes are:

| Case | Extra cooler removal W | Heater correction W | Remove 1D test source W | CFD test-section sink W | Known correction W |
| --- | ---: | ---: | ---: | ---: | ---: |
| Salt 2 | 89.973 | 22.181 | 37.000 | 5.680 | 154.833 |
| Salt 3 | 101.032 | 24.345 | 37.000 | 10.545 | 172.921 |
| Salt 4 | 115.351 | 27.113 | 37.000 | 16.769 | 196.232 |

## Four Remedy Paths Tried

All replays used the existing Fluid `solve_temperature_periodicity()` at the CFD
mdot.  They are fixed-mdot thermal replays, not full predictive hydraulic
solutions.  No Fluid repo files were edited.

### P1: Prescribe CFD Cooler Duty Only

Setup:

- Keep the current heat sources: heater imposed duty plus 37 W test-section
  source.
- Replace the predictive air-side HX duty with the CFD cooler wallHeatFlux
  magnitude.
- Keep internal ambient-loss model active.

Result:

| Case | Tmean error K | Loop dT error K | qhx W |
| --- | ---: | ---: | ---: |
| Salt 2 | +6.219 | +0.138 | 136.351 |
| Salt 3 | +4.453 | -0.109 | 150.770 |
| Salt 4 | +2.697 | -0.174 | 169.227 |

Interpretation: this is the strongest single remedy.  It nearly closes loop
delta T and reduces mean error from about 64 K to about 4.5 K average, but it
does not pass the strict `2 K` mean-temperature gate.

### P2: Heater WallHeatFlux, No Test-Section Source

Setup:

- Use heater interface wallHeatFlux as the source.
- Remove the 37 W 1D test-section source.
- Keep predictive air-side HX and internal ambient losses.

Result:

| Case | Tmean error K | Loop dT error K | qhx W |
| --- | ---: | ---: | ---: |
| Salt 2 | +31.507 | -1.493 | 39.262 |
| Salt 3 | +33.847 | -1.735 | 42.728 |
| Salt 4 | +36.937 | -1.824 | 46.963 |

Interpretation: source correction helps substantially, but cannot replace the
cooler correction.  It also worsens loop delta T because the predictive cooler
duty remains too small.

### P3: Heater WallHeatFlux Plus Test-Section Net Sink

Setup:

- Use heater interface wallHeatFlux.
- Treat CFD test-section wallHeatFlux as a negative local source.
- Keep internal ambient losses active.

Result:

| Case | Tmean error K | Loop dT error K | qhx W |
| --- | ---: | ---: | ---: |
| Salt 2 | +28.373 | -1.437 | 38.544 |
| Salt 3 | +28.326 | -1.643 | 41.456 |
| Salt 4 | +28.679 | -1.694 | 45.048 |

Interpretation: this improves P2 by adding the observed quartz/test-section sink,
but still leaves the model too hot because the cooling jacket is still
under-removing heat.

### P4: Full Patch-Ledger Fixed-Q Replay

Setup:

- Use heater wallHeatFlux as source.
- Prescribe cooler, test-section, passive ambient, and grouped junction losses
  from CFD wallHeatFlux.
- Disable predictive HX duty by setting imposed qhx to zero; losses are carried
  through prescribed segment losses.

Result:

| Case | Tmean error K | Loop dT error K | Status |
| --- | ---: | ---: | --- |
| Salt 2 | -168.296 | +0.512 | fixed-Q mean under-anchored |
| Salt 3 | -194.853 | +0.263 | fixed-Q mean under-anchored |
| Salt 4 | +51.042 | +0.196 | fixed-Q mean under-anchored |

Interpretation: this is not a successful mean-temperature remedy.  A fully
fixed-Q ledger makes the absolute mean temperature under-anchored in the 1D
periodicity solve because net source and sink are nearly balanced independent
of temperature.  The useful result is that loop delta T becomes close to CFD,
but a paper-grade replay must reconstruct temperature-dependent boundary
networks, not only prescribe fixed total losses.

## Pipe Walls and Cooler Modeling Assessment

Current Fluid state from solver inspection:

- Ambient pipe-wall losses include internal convection, pipe wall conduction,
  insulation resistance, outside natural convection, and optional radiation.
- The active cooling jacket uses a separate air-side heat-exchanger model with
  annulus hydraulic diameter, air mass flow, internal salt HTC, wall resistance,
  air HTC, and NTU effectiveness.
- For `predictive_airside_hx`, the cooler duty is predicted, not imposed.

Scientific assessment:

- Pipe walls are represented, but the CFD contract requires per-segment
  reconstruction: insulated pipe legs, bare quartz test section, and exact
  patch roles.  A global 1D insulation scalar is too blunt for this paper-grade
  comparison.
- The cooler is not currently removing the CFD-observed energy.  The
  discrepancy is about 90-115 W beyond the current predictive qhx.  The cooling
  jacket path must be audited before further friction tuning.
- P1 indicates the correct amount of cooling removal nearly closes mean T and
  loop dT.  Therefore the cooler-removal magnitude and/or cooling-jacket mapping
  is the highest-priority remedy.

## qr Radiation Term

Observed:

- CFD boundary metadata includes emissivity on `rcExternalTemperature` patches.
- The scenario contract reports no `radiationProperties` and no `qr`/`G` field.
- The heat ledger therefore records `radiation_present=False` and
  `surface_emissivity_bc_metadata_present_but_no_qr_radiation_output`.

What is missing:

- A separate patchwise radiation heat-rate term.
- Evidence whether OpenFOAM's boundary condition computed radiation implicitly,
  used emissivity metadata only inside a mixed external-temperature law, or
  simply retained emissivity metadata without a volume radiation solve.

How to improve:

1. Inspect the exact OpenFOAM boundary-condition implementation and case
   dictionaries for `rcExternalTemperature`.
2. Determine whether patch heat flux already includes any radiative exchange.
3. If separate radiation accounting is required, add/export a patchwise radiation
   diagnostic or run a controlled postprocess/solver variant with `qr` or an
   equivalent patch term.
4. In 1D, keep radiation as a separate modeled component:
   `q_rad = epsilon sigma A (T_s^4 - T_sur^4)` or linearized `h_rad`, but do not
   add it on top of CFD wallHeatFlux unless wallHeatFlux is proven to exclude it.

The immediate rule is: do not double count emissivity.  Surface emissivity is not
itself a separate measured `qr` term.

## Fixed-mdot / Frozen-Hydraulics Solver Plan

The issue:

`solve_case()` currently searches mdot to close pressure residual.  That is
correct for predictive operation, but bad for this thermal replay because
thermal changes move density, viscosity, buoyancy, pressure loss, mdot, Re, and
temperature together.

Required mode:

- Hold `mdot = CFD mdot`.
- Solve only thermal periodicity.
- Compute pressure residual afterward as a diagnostic.
- Report this as thermal replay, not predictive hydraulics.

Proposed API:

```python
fixed_mdot_kg_s: Optional[float] = None
hydraulic_solution_mode: str = "predictive_pressure_root"  # or fixed_mdot_thermal_replay
```

Required tests:

- Fixed-mdot result uses the exact target mdot.
- Fixed-mdot `ModelResult` thermal state matches direct
  `solve_temperature_periodicity()` at the same mdot.
- Nonzero pressure residual is reported but not used to reject thermal replay.
- Reporting separates predictive mdot scores from fixed-mdot thermal scores.

Detailed plan:

- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_solver_plan.md`

## Parallel Agent Prompts

Ready helper prompts are written in:

- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/parallel_agent_prompts.md`

They cover:

- Cooler/HX duty audit.
- Source/test-section contract audit.
- Radiation/`qr` reconstruction.
- Fixed-mdot Fluid solver design.

## Validation

Commands:

```bash
python tools/analyze/build_thermal_mismatch_remedy_deep_dive.py
python3.11 -m unittest tools.analyze.test_thermal_mismatch_remedy_deep_dive
python3.11 -m py_compile tools/analyze/build_thermal_mismatch_remedy_deep_dive.py tools/analyze/test_thermal_mismatch_remedy_deep_dive.py
```

Results:

- Builder completed with 15 fixed-mdot replay rows.
- Tests passed: 3/3.
- Syntax check passed.

## Recommended Execution Order

1. Assign Agent A to audit and repair the cooler/HX duty model first.
2. Assign Agent D in parallel to implement the formal fixed-mdot replay mode.
3. Assign Agent B to reconcile heater wallHeatFlux versus imposed duty and
   quartz/test-section source semantics.
4. Assign Agent C to resolve `qr`/radiation accounting before adding any
   radiation term to 1D.
5. After A and D land, rerun P1 as a formal Fluid scenario and then combine
   source/test-section corrections.  Do not run model-form bakeoff until the
   fixed-mdot replay passes the mean-T and loop-dT gate.
