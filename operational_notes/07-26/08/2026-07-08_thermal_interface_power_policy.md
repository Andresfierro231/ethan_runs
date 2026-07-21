# Thermal Interface Power Policy for 3D-to-1D Comparisons

Date: `2026-07-08`
Task: `AGENT-213`
Role: Coordinator / Writer

## Purpose

This note records the required comparison contract for all agents comparing the
3D CFD runs against the 1D model. It resolves the heater and cooler power
interpretation issue found during the July 8 thermal mismatch work.

## Required policy

When comparing a 3D CFD state to a 1D state, use the heat that actually crosses
the CFD fluid boundary:

- Heater source: use the 3D heater patch `wallHeatFlux` integral, reported in
  `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/heater_values.csv`
  as `heater_wallHeatFlux_input_W`.
- Cooler sink: use the 3D cooler patch `wallHeatFlux` sink magnitude, reported
  in `work_products/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv`
  as the `cooler` `cooler_removed_duty_W` or equivalently
  `-wallHeatFlux_integral_W`.
- Do not use idealized resistor wattage or imposed electrical duty as the 1D
  fluid heat input for CFD-informed comparison.
- Do not use the current idealized 1D cooler-capacity prediction as the CFD
  cooler truth for CFD-informed comparison.

The `wallHeatFlux` sign convention in the July 8 thermal boundary contract is
positive into the fluid and negative out of the fluid.

## Current evidence

Heater values from
`work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/heater_values.csv`:

| Case | Imposed heater duty W | Heater wallHeatFlux into fluid W | Difference W | Fluid-entry fraction |
| --- | ---: | ---: | ---: | ---: |
| Salt 2 | 265.700 | 243.519 | 22.181 | 0.9165 |
| Salt 3 | 297.500 | 273.155 | 24.345 | 0.9182 |
| Salt 4 | 337.600 | 310.487 | 27.113 | 0.9197 |

Cooler values from the July 8 thermal boundary contract and fixed-mdot replay:

| Case | Current 1D cooler removal W | CFD cooler removal W | Difference W |
| --- | ---: | ---: | ---: |
| Salt 2 | 46.292 | 136.351 | 90.059 |
| Salt 3 | 49.663 | 150.770 | 101.107 |
| Salt 4 | 53.472 | 169.227 | 115.755 |

The fixed-mdot replay in
`work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_replay_results.csv`
showed that replacing the current 1D cooler duty with the CFD cooler duty
reduced mean-temperature errors to 6.219 K, 4.453 K, and 2.697 K for Salt 2,
Salt 3, and Salt 4. This is strong evidence that the cooler interface heat
contract is a dominant current mismatch.

## Interpretation

The resistor-imposed duty is not equal to heat delivered to the fluid. Some
dissipated electrical power can remain in solids, leak to surroundings, or be
represented through the CFD boundary/solid setup in a way that does not appear
as heater patch heat into the fluid. Therefore, the 1D model should not be
penalized against the larger idealized electrical wattage when the 3D CFD fluid
actually receives the smaller heater `wallHeatFlux`.

The same principle applies to the cooler. For CFD-informed validation, the
cooler sink is the heat removed from the CFD fluid through the cooler patches.
The present idealized 1D cooler model removes much less heat than the CFD cooler
patches. That discrepancy is a predictive-modeling problem, not a reason to use
the idealized cooler value as the CFD comparison truth.

## Thesis and paper limitation

Until the heater and cooler predictive submodels are validated, any 1D replay
that prescribes the CFD heater `wallHeatFlux` and CFD cooler heat removal should
be described as a CFD-informed thermal replay. It is useful for isolating
hydraulics, loop thermal allocation, and model-form errors, but it is not yet a
fully predictive physical-system simulation from resistor wattage, cooler
hardware settings, ambient conditions, and geometry alone.

If this limitation is still present in the thesis or journal paper, disclose it
plainly:

- The model comparison uses realized CFD interface heat transfer as boundary
  input.
- Predicting how much electrical resistor power reaches the fluid is deferred
  to a heater-coupling submodel.
- Predicting how much heat the cooler removes from the fluid is deferred to a
  cooler/cooling-jacket submodel.
- Reported agreement from CFD-informed replays should not be interpreted as a
  full hardware-input prediction unless the predictive submodels are also
  active and validated.

## Future goal: predict heater heat entering the fluid

Board row: `TODO-PREDICT-HEATER-FLUID-FRACTION`.

Candidate approaches:

- Fit and validate a first-pass heater efficiency
  `eta_heater = heater_wallHeatFlux_input_W / heater_imposed_duty_W` using the
  Salt 2/3/4 values above and any corrected-Q perturbation cases admitted later.
- Build a physics-based resistance/storage network from resistor to wall to
  fluid and to ambient, including insulation, external convection, solid thermal
  storage over the retained window, and any known heater contact geometry.
- Use patchwise heat ledgers and span enthalpy residuals to close the heater
  segment energy balance before fitting adjustable parameters.
- Treat nominal cases and perturbation cases as separate fit and validation
  groups so the model is not merely interpolating the same window it was tuned
  on.

Criteria for success:

- Predeclare fit cases and held-out validation cases.
- Predict heater `wallHeatFlux` into the fluid within a documented tolerance,
  such as <=5% or <=10 W, on held-out cases.
- Preserve energy balance between imposed electrical power, fluid heat input,
  solid/ambient loss, and storage within stated uncertainty.
- Record all source paths, time windows, and case-admission flags.

## Future goal: predict cooler heat removed from the fluid

Board row: `TODO-PREDICT-COOLER-REMOVAL`.

Candidate approaches:

- Audit the cooling-jacket geometry and boundary contract: active length,
  reducer participation, annulus dimensions, coolant or air-side assumptions,
  external coefficients, and whether the 1D segment map matches the CFD cooler
  patch group.
- Build a UA or epsilon-NTU model from fluid bulk temperature, wall or coolant
  temperature, active area, and flow-side heat-transfer assumptions.
- Split the cooler sink into main cooler and reducer contributions if the CFD
  patch ledger shows meaningful reducer heat removal.
- Validate against nominal Salt 2/3/4 and later corrected-Q perturbation cases
  without using CFD cooler duty as an input.

Criteria for success:

- Predeclare fit and held-out validation cases.
- Predict CFD cooler heat removal within a documented tolerance, such as
  <=5-10% or <=10 W.
- In fixed-mdot thermal replay, match CFD mean temperature and loop Delta T
  within the formal thermal gate without prescribing CFD cooler duty.
- Preserve a separate diagnostic comparing predicted cooler removal to CFD
  `wallHeatFlux` so failure modes remain visible.

## Radiation handling

The current Salt 2/3/4 3D CFD evidence has surface-emissivity metadata but no
separate OpenFOAM `qr` radiation output term. Therefore:

- Do not add a radiation correction on top of CFD `wallHeatFlux` when doing
  CFD-informed comparison; that would risk double counting heat loss.
- Keep the no-`qr` caveat attached to CFD-derived thermal ledgers.
- The 1D model should still have radiation heat-loss capability for sensitivity
  studies and forward prediction.

Future 1D radiation work should implement or verify nonlinear or linearized
Stefan-Boltzmann segment losses with emissivity, surroundings temperature, and
surface area. It should report radiation as a separate energy-ledger term and
run radiation on/off sensitivity tables across the Salt cases. Analytic tests
against a known surface or cylinder radiation calculation are required before
the feature is used for paper claims.

## Agent checklist

Before publishing any 3D-to-1D thermal comparison:

1. Confirm whether the run is CFD-informed or fully predictive.
2. For CFD-informed comparison, set heater input from CFD heater
   `wallHeatFlux`, not resistor wattage.
3. For CFD-informed comparison, set cooler removal from CFD cooler
   `wallHeatFlux`, not current idealized 1D cooler capacity.
4. Keep radiation off or explicitly separated when matching current CFD no-`qr`
   cases.
5. State the limitation if electrical-to-fluid heater coupling or
   cooler-removal prediction is not independently validated.
