# Salt Closure / Correlation Package Math Companion

Generated: `2026-06-18`

This note documents the derived quantities used by
`tools/analyze/build_ethan_salt_closure_correlation_package.py`.

## Straight-section hydraulic screening

The package reuses the additive June 17 sectionwise pressure closure:

`Delta p_hydro = Delta p_wall + integral rho g dot t_hat ds`

and retains:

- signed apparent Darcy factor from the hydro-corrected section loss
- direct wall-registered `p_rgh` Darcy proxy
- shear-based Darcy proxy from the established streamwise package

The Salt straight-section fit status is:

- `candidate` when the section is net dissipative (`Delta p_hydro > 0`),
  thermal support fraction is at least `0.75`, direct and shear friction
  proxies are both positive, and `0.5 <= direct/shear <= 2.0`
- `screening_only` when the section is buoyancy-aided, support-limited, or the
  direct/shear ratio is materially mismatched
- `do_not_fit` when the direct or shear proxy is nonpositive or missing

These statuses are correlation-fit gates, not claims that the underlying raw
reduction is invalid.

## Feature K_eff

Feature `K_eff` is inherited from the additive June 17 package:

`K_eff = Delta p_feature,residual / q_ref`

where the residual closure is still based on the stored `p_rgh` feature path.
The current package treats positive residual `K_eff` as a fit candidate and
negative `K_eff` as screening-only because it likely reflects subtraction and
support ambiguity rather than a physically useful minor-loss coefficient.

## Branch thermal usability

The branch usability mask follows the scrutiny thresholds:

- `candidate` when usable fraction `>= 0.90`, warning fraction `<= 0.10`, and
  minimum resolved `|T_bulk - T_wall| >= 0.50 K`
- `do_not_fit` when usable fraction `< 0.75`, warning fraction `> 0.25`, or
  minimum resolved `|T_bulk - T_wall| < 0.25 K`
- `screening_only` otherwise

These thresholds determine whether an effective thermal ratio is suitable for a
correlation input table. They do not claim intrinsic local HTC closure quality.

## Enthalpy residual

For each Salt span, the package reuses:

`Delta H_leg = mdot cp (T_out - T_in)`

`Q_wall,leg = integral q'_wall ds`

and reports the normalized residual

`r_H = |Delta H_leg - Q_wall,leg| / |Q_wall,leg|`

The current status thresholds are:

- `candidate` when `r_H <= 0.15`
- `screening_only` when `0.15 < r_H <= 0.30`
- `do_not_fit` when `r_H > 0.30`

## Heat-loss partition indicators

The package reports case-level Salt indicators using the June 9 heat audit:

- ambient proxy mean
- noncooling ambient proxy mean
- cooling branch total removal mean
- cooling branch excess mean
- junction loss mean

These are not a full internal-convection / wall-conduction / external-radiation
decomposition. They are screening indicators for how much heater power leaves
through intended versus parasitic channels.
