# Master's Thesis Story Draft

## Working Chapter Argument

The CFD-to-1D closure workflow should be presented as an evidence reduction
pipeline. The main contribution is not a single new coefficient. It is the
construction of auditable CFD observables that can be mapped onto separate 1D
terms: reversible buoyancy, irreversible distributed resistance, developing-flow
excess, feature/minor losses, thermal boundary exchange, and recirculation
regime diagnostics.

## Numerical Analysis Framing

The July 8 pressure ledger supplies span-level hydraulic decomposition with
source windows and admission flags. The July 8 patchwise heat ledger supplies
the corresponding wall-flux accounting plus non-junction segment enthalpy
residuals from endpoint bulk-temperature extraction. The closure observation
table provides the row-level contract needed to
separate fit targets from validation diagnostics.

## Current Scientific Findings

- July 8 pressure ledger contributes 18 admitted Salt 2/3/4 span rows with explicit buoyancy, distributed loss, development/reset, minor-loss upper-bound, and residual terms.
- July 8 patchwise heat ledger contributes 15 patch-group rows; aggregate heater input, cooler/passive removals, and segment enthalpy residuals are available as validation diagnostics.
- Heat enthalpy residuals are populated for non-junction spans; current absolute residuals range from 36.7 W to 162.7 W.
- F1 mdot errors are positive across Salt 2/3/4 (9.7% to 18.0%), while F3 Shah apparent narrows the range (-0.9% to 3.7%).
- F4 leg-class mdot errors are negative across Salt 2/3/4 (-24.7% to -23.2%), consistent with over-stiffening in the current 1D run.
- F5/Ri screen has 4 leg classes either deactivated or excluded; active F5 coefficients are zero in the current package.
- Upcomer backflow fraction decreases across the admitted Salt series from 27.8% to 17.2% as Re increases.
- Corrected Salt live monitor includes 14 status rows; 4 need special gate scrutiny and 2 are marked investigate.

## Interpretation For Thesis Prose

- The strongest presentable story is decomposition and admission discipline: the workflow now separates what CFD directly shows from terms that can become 1D closures.
- Developing-flow friction is already a better practical baseline than fully developed F1 for the current Salt 2/3/4 mdot screen.
- The remaining mdot gap cannot be assigned to friction alone because the heat ledger now shows first-order segment enthalpy residuals and a net-sink test-section wall flux.
- The upcomer should be treated as a regime problem, not as an ordinary single-stream pipe-friction span, until recirculation onset is better bounded.
- Corrected Salt perturbations are promising for expanding the operating envelope but remain outside closure fitting until formal gate requalification.

## Remaining Threats To Validity

- No mesh/GCI uncertainty is attached to the presented QOIs yet; all admitted rows remain coarse_no_gci.
- Corrected Salt perturbation rows are status-only until the gate completes and special-scrutiny rows are dispositioned.
- Thermal enthalpy residuals are available for non-junction spans, but upcomer rows are recirculation diagnostics and cooler endpoints only partially bracket the cooler.
- F5/Ri cannot be promoted without more admitted operating points spanning a wider Ri/Re domain.

## Proposed Thesis Next Steps

- Use this chart package for tomorrow's high-level evidence story: pressure decomposition, heat accounting, friction screens, upcomer regime, and gate status.
- Use the enthalpy-residual chart to separate thermal-state mismatch from pressure and mdot model-form scores.
- Build the model-form bakeoff from the closure observation table, scoring pressure distribution, mdot, and thermal-state mismatch separately.
- When corrected Salt gate results land, refresh the status chart first, then decide which rows may enter perturbation trend and F5/Ri refit packages.
- Pursue mesh/GCI intake before making paper-grade coefficient claims.

## Draft Thesis Paragraph

The present CFD evidence indicates that the TAMU loop cannot be reduced to a
single fully developed friction closure without losing key physics. In the
heated and cooled branches, pressure behavior contains both reversible
density-gradient forcing and irreversible mechanical loss. In the upcomer,
recirculation violates the single-stream assumption behind ordinary pipe
friction. In the thermal model, wall-flux accounting shows that passive and
junction losses, as well as net test-section heat removal, are large enough to
affect the buoyancy driver. Therefore the predictive 1D model should be
validated through separate pressure-distribution, heat-balance, mass-flow, and
regime-classification scores rather than through mass flow alone.
