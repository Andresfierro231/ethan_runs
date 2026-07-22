# Fixed-mdot / Frozen-hydraulics Solver Plan

## Issue

The current Fluid `solve_case()` always searches mdot to close the pressure residual. That is correct for predictive hydraulic mode, but it confounds the thermal mismatch investigation: changing thermal losses changes density, viscosity, buoyancy, pressure losses, mdot, Re, and temperature at the same time.

For the thermal replay we need a mode that holds mdot at the CFD target and solves only thermal periodicity. The pressure residual should still be reported, but not used to move mdot.

## Proposed API

Add to `ScenarioConfig`:

```python
fixed_mdot_kg_s: Optional[float] = None
hydraulic_solution_mode: str = "predictive_pressure_root"  # or "fixed_mdot_thermal_replay"
```

or equivalently add a separate `solve_case_fixed_mdot(...)` wrapper if we want to avoid expanding the public scenario schema immediately.

## Algorithm

1. Build geometry and scenario segments exactly as `solve_case()` does.
2. Resolve optional 3D source/loss contracts exactly as `solve_case()` does.
3. Set `mdot = fixed_mdot_kg_s`.
4. Call `solve_temperature_periodicity(...)`.
5. Compute buoyancy and distributed/minor pressure terms using the resulting thermal state.
6. Return a `ModelResult` with:
   - `mdot_kg_s = fixed_mdot_kg_s`
   - `pressure_residual_Pa` reported but not rooted
   - `root_status` indicating thermal periodicity status, not pressure-root acceptance
   - an explicit metadata flag such as `hydraulic_solution_mode=fixed_mdot_thermal_replay`

## Assumptions

- CFD mdot is the target hydraulic state for the replay.
- Thermal periodicity remains the proper steady 1D thermal closure.
- Pressure residual is diagnostic in this mode.
- This mode is not a predictive mdot model and must not be scored as such.

## Limitations

- It does not prove the hydraulic closure is correct.
- It may suppress real coupling between thermal losses and buoyancy-driven flow.
- It depends on the CFD mdot/admission quality.
- If prescribed patch losses are mapped coarsely to parent segments, local temperatures can still be wrong even if loop mean is improved.

## Required Tests

1. Fixed-mdot result uses the exact requested mdot.
2. Fixed-mdot thermal state matches direct `solve_temperature_periodicity()` at the same mdot.
3. Pressure residual is reported and nonzero cases remain accepted only as thermal replay, not predictive hydraulics.
4. Scenario validation rejects `fixed_mdot_kg_s <= 0`.
5. Reporting layer separates predictive mdot scores from fixed-mdot thermal scores.
