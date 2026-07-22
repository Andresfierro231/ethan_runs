# Presentation Story Draft

## One-Slide Thesis

The CFD postprocessing is now strong enough to show why a predictive 1D model
must be built from decomposed terms rather than a single tuned friction
coefficient: pressure, heat-path, and upcomer-regime effects are all visible and
must be admitted or excluded explicitly.

## Suggested Slide Sequence For Tomorrow

1. **Evidence contract.** Salt 2/3/4 Jin are admitted mainline evidence; corrected
   Salt is status-only; all rows still need mesh/GCI before coefficient claims.
2. **Pressure decomposition.** Show `pressure_decomposition_by_span.svg`.
   Message: raw `p_rgh` slopes are not friction; buoyancy, mechanical loss,
   development/reset, minor losses, and recirculation flags are now separated.
3. **Heat accounting.** Show `heat_source_sink_by_patch_group.svg`.
   Message: the thermal boundary matters first order; the test section is a net
   heat sink in the wall-flux accounting.
4. **Thermal residuals.** Show `heat_enthalpy_residual_by_segment.svg`.
   Message: span endpoint temperatures now expose segment residuals; upcomer and
   cooler residuals stay diagnostic because of recirculation and bracketing limits.
5. **Friction screen.** Show `friction_form_mdot_error.svg` and optionally
   `friction_per_leg_pressure_drop.svg`.
   Message: F3 Shah apparent currently performs best in mdot, while F4
   over-stiffens. Do not claim final mdot predictivity until thermal replay is fixed.
6. **F5/Ri honesty.** Show `f5_ri_screen_coefficients.svg`.
   Message: the current three-point admitted dataset does not support a Ri
   multiplier; the framework waits for gated perturbations.
7. **Upcomer regime.** Show `upcomer_backflow_vs_re.svg`.
   Message: the upcomer is a recirculating mixed-convection regime, not ordinary
   pipe friction.
8. **What is still moving.** Show `corrected_salt_gate_status.svg`.
   Message: perturbations may expand the range, but they are not admitted yet.

## Observed Facts To Say Out Loud

- July 8 pressure ledger contributes 18 admitted Salt 2/3/4 span rows with explicit buoyancy, distributed loss, development/reset, minor-loss upper-bound, and residual terms.
- July 8 patchwise heat ledger contributes 15 patch-group rows; aggregate heater input, cooler/passive removals, and segment enthalpy residuals are available as validation diagnostics.
- Heat enthalpy residuals are populated for non-junction spans; current absolute residuals range from 36.7 W to 162.7 W.
- F1 mdot errors are positive across Salt 2/3/4 (9.7% to 18.0%), while F3 Shah apparent narrows the range (-0.9% to 3.7%).
- F4 leg-class mdot errors are negative across Salt 2/3/4 (-24.7% to -23.2%), consistent with over-stiffening in the current 1D run.
- F5/Ri screen has 4 leg classes either deactivated or excluded; active F5 coefficients are zero in the current package.
- Upcomer backflow fraction decreases across the admitted Salt series from 27.8% to 17.2% as Re increases.
- Corrected Salt live monitor includes 14 status rows; 4 need special gate scrutiny and 2 are marked investigate.

## Interpretation To Keep Conservative

- The strongest presentable story is decomposition and admission discipline: the workflow now separates what CFD directly shows from terms that can become 1D closures.
- Developing-flow friction is already a better practical baseline than fully developed F1 for the current Salt 2/3/4 mdot screen.
- The remaining mdot gap cannot be assigned to friction alone because the heat ledger now shows first-order segment enthalpy residuals and a net-sink test-section wall flux.
- The upcomer should be treated as a regime problem, not as an ordinary single-stream pipe-friction span, until recirculation onset is better bounded.
- Corrected Salt perturbations are promising for expanding the operating envelope but remain outside closure fitting until formal gate requalification.

## Do Not Overclaim

- No mesh/GCI uncertainty is attached to the presented QOIs yet; all admitted rows remain coarse_no_gci.
- Corrected Salt perturbation rows are status-only until the gate completes and special-scrutiny rows are dispositioned.
- Thermal enthalpy residuals are available for non-junction spans, but upcomer rows are recirculation diagnostics and cooler endpoints only partially bracket the cooler.
- F5/Ri cannot be promoted without more admitted operating points spanning a wider Ri/Re domain.

## Ask / Next Work

- Use this chart package for tomorrow's high-level evidence story: pressure decomposition, heat accounting, friction screens, upcomer regime, and gate status.
- Use the enthalpy-residual chart to separate thermal-state mismatch from pressure and mdot model-form scores.
- Build the model-form bakeoff from the closure observation table, scoring pressure distribution, mdot, and thermal-state mismatch separately.
- When corrected Salt gate results land, refresh the status chart first, then decide which rows may enter perturbation trend and F5/Ri refit packages.
- Pursue mesh/GCI intake before making paper-grade coefficient claims.
