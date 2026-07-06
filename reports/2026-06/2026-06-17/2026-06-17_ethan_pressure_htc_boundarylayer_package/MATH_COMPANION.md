# Ethan Pressure / HTC / Boundary-Layer Math Companion

Generated: `2026-06-17`

This note documents the definitions implemented by
`tools/analyze/build_ethan_pressure_htc_boundarylayer_package.py`.

## Pressure Closure

For a straight repaired section, the explicit hydro-corrected pressure loss is

`Delta p_loss = p_start - p_end + integral rho(s) g dot t_hat_flow(s) ds`

where `t_hat_flow` points along the inferred flow direction from the existing
June 15 streamwise package. The additive package also reports two cross-checks:

- endpoint `p_rgh` loss: `p_rgh,start - p_rgh,end`
- integrated `p_rgh` gradient from the existing major-loss package

The section closure residuals are:

- `Delta p_loss - Delta p_rgh,endpoint`
- `Delta p_loss - integral (dp_rgh/ds) ds`

These are diagnostic residuals, not forced-to-zero constraints.

## Apparent Friction Factor

The section-local apparent Darcy factor uses the explicit hydro-corrected loss:

`f_D,app,local = Delta p_loss * 2 D_h / (rho_b U_b^2 L)`

The loop-reference normalization uses the same numerator but a case-level loop
dynamic-head reference:

`f_D,app,loop = Delta p_loss * 2 D_h / (rho_loop U_loop^2 L)`

The package also reports a core-only shear comparison from the existing shear
reduction, restricted to straight main-pipe spans and excluding end zones near
junctions and the test-section transitions.

## Feature K_eff

For corners and the quartz test-section complex, the additive package reuses the
existing `p_rgh`-based feature residual closure:

`K_eff = Delta p_minor,residual / q_ref`

with

- `Delta p_minor,residual = Delta p_feature,p_rgh - Delta p_adjacent_major,ref`
- `q_ref = 0.5 rho_ref U_ref^2`

`rho_ref` and `U_ref` are built from the adjacent major-span section means.

## Bulk Temperature and HTC / Nu

For Salt-family cases, the stored June 15 bulk temperature is exact for the
requested `rho*u*cp` weighting because `cp(T)` is effectively constant.

For Water-family cases, this additive package recomputes `T_bulk` from the
preserved cut-plane surfaces stored in the June 15 raw extraction package. It
retains the original connected-region support logic, but replaces the stored
mass-flux-weighted definition with the requested

`T_bulk = (integral rho u_n cp T dA) / (integral rho u_n cp dA)`

using the water `rho(T)` and `cp(T)` polynomials from `case_config.yaml`.

The package also records the comparison against the older stored method:

- old stored bulk: positive aligned `rho*u_n` weighting
- exact flow-only rebuild: positive aligned `rho*u_n` weighting rebuilt from the
  preserved per-face surfaces
- exact requested rebuild: positive aligned `rho*u_n*cp` weighting rebuilt from
  the preserved per-face surfaces

Local wall-side transfer fields use

`h(s,theta) = q''_w / (T_w - T_bulk)`

`Nu(s,theta) = h D_h / k(T_bulk)`

The package keeps the sign convention from the wall heat-flux field. Rows with
`|T_w - T_bulk| < 0.25 K` are masked.

Area-ratio section HTC uses

`h_A = (integral q''_w dA) / (integral (T_w - T_bulk) dA)`

and

`Nu_A = h_A D_h / k(T_bulk)`

## Enthalpy Balance

For each major span, the package reports

`Delta H_leg = mdot * cp(T_bar) * (T_out - T_in)`

and compares that against the integrated wall heat from the existing
streamwise reduction:

`Q_wall,leg = integral q'_w(s) ds`

The closure residual is `Delta H_leg - Q_wall,leg`.

## Boundary-Layer Ratios

The boundary-layer package is still a first-pass landmark method. It uses the
existing wall-to-centerline landmark reductions and reports:

- `delta99_u / D_h`
- `delta99_T / D_h`
- `delta99_T / delta99_u`

These are reported as comparative boundary-thickness proxies on straight
sections. They are not claimed to be full circumferential boundary-layer maps.
