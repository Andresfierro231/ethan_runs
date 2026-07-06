# Methods Interpretation

## Scope

This note tightens the interpretation layer on top of the June 17 streamwise
transport math companion. It does not redefine the implemented formulas. It
explains how those formulas should be read scientifically when the resulting
transport quantities are used for model dependency construction.

## What the effective hydraulic quantities mean

The shear-based hydraulic reduction is a wall-stress reduction. It projects
wall shear onto the repaired streamwise tangent, area-averages the projected
streamwise magnitude, and then converts that wall-stress surrogate into
Darcy/Fanning form with the current hydraulic-diameter and bulk-speed
surrogates. It is therefore a wall-stress-derived hydraulic indicator, not a
direct measurement of centerline pressure drop.

The direct hydraulic reduction is a wall-registered pressure diagnostic. It
area-averages wall `p_rgh` or `p` in each streamwise bin, finite-differences
those wall means along the repaired coordinate, and then converts the result
into Darcy/Fanning form with the same surrogate geometry. It is therefore a
wall-pressure-derived indicator, not a control-volume momentum closure.

These two hydraulic paths should agree on the broad pressure-drop direction and
the main accumulation regions before they are used as model evidence.

## Why direct and shear hydraulic reductions may disagree

Direct and shear reductions can disagree for at least four distinct reasons:

1. They use different observables. Wall shear is local traction data. Direct
   `p_rgh` is a finite-differenced wall-pressure field.
2. The direct path is vulnerable to branchwise differencing noise when the net
   `p_rgh` drop is small. Mixed positive and negative local derivatives can
   average toward zero even when the branch-end cumulative drop is positive.
3. The direct path depends on flow-direction alignment. If `flow_alignment_sign`
   is inconsistent across retained windows or bins, branch means can inherit a
   sign-registration problem rather than a real physics reversal.
4. `p` and `p_rgh` are not interchangeable in buoyant loops. `p` is dominated
   by hydrostatic head; `p_rgh` is the friction-scale direct diagnostic.

The two highest-priority Water contradictions illustrate these failure modes.

- Water 1 left_lower_leg: Treat the contradiction as a resolved exclusion rather than a usable hydraulic dependency. The direct p_rgh signal is about one order of magnitude smaller than the shear-implied branch drop (terminal ratio 0.104), and the mean direct gradient is effectively a weak-signal average over mixed-sign local derivatives.
- Water 2 left_lower_leg: Do not use this branch for Water or cross-family hydraulic dependency construction until the sign-registration path is audited. The direct p_rgh signal is weak relative to the shear estimate and the mixed per-row alignment sign means the current branch mean is not mechanically traceable to one consistent pressure-drop convention.

Disagreement in pressure-drop direction is serious because it means the
postprocessed branch result is not robust even at the sign level. Those rows
must be excluded from cross-family hydraulic dependency construction until the
sign convention or aggregation issue is resolved.

## Why small |T_bulk - T_wall| causes HTC, UA', and R'_th blowups

The current effective thermal quantities are ratios:

- `h_eff = |q''_w| / |T_bulk - T_wall|`
- `UA'_eff = |q'_w| / |T_bulk - T_wall|`
- `R'_th = 1 / UA'_eff`

When the resolved branch-scale driving temperature approaches zero, the ratio
becomes extremely sensitive to small numerator or denominator perturbations.
This is not a cosmetic plotting issue. It is a structural property of the
effective reduction.

For that reason, a large reported effective HTC does not automatically mean a
physically stronger local transfer mechanism. It may simply mean:

- the branch is operating with a weak resolved thermal driving force,
- the selected bulk region is only marginally supported,
- the denominator is small enough that ratio noise is amplified.

The Water left-side branches and several upper-leg rows show exactly this
behavior. They must be treated as support-limited diagnostics rather than
fittable closure targets.

## Why R'_th can look attractive but still be support-limited

`R'_th` is often visually appealing because it converts large effective-HTC
swings into a smaller numerical scale. That can make the curve look calmer.
But `R'_th` is not independent information. It is the reciprocal of `UA'_eff`
and inherits the same support path, the same branch masking, and the same weak
Delta-T failure mode.

A numerically smooth `R'_th` value is therefore not enough to promote a branch.
The support fraction, the minimum resolved `|T_bulk - T_wall|`, and the branch
warning breakdown still control whether the quantity is model-ready.

## Why momentum resistance is only a proxy

The current momentum-resistance quantity is local `dp/ds` divided by `mdot`. It
is useful as a diagnostic because it places the pressure-gradient reductions on
a mass-flow-normalized scale. But it is still downstream of the same direct or
shear pressure surrogate and therefore cannot be treated as a directly measured
resistance law.

If the underlying hydraulic reduction is contradictory or support-limited, the
momentum-resistance proxy is also contradictory or support-limited.

## Why support fraction is not cosmetic

Support fraction is not a presentation filter. It tells you whether the branch
summary is actually built from enough usable rows to represent the branch.

- Low usable fraction means the branch summary is being carried by a minority
  of the retained rows.
- Small `|T_bulk - T_wall|` means the ratio denominator is weak.
- Large masked fractions mean the effective metric exists numerically but is
  not stable enough to generalize.

These are scientific trust limits, not plotting preferences.

## Why branch promotion gates are necessary

Branch promotion gates exist because not every branch supports the same quality
of reduced quantity.

- Salt safe subset: `left_lower_leg`, `test_section_span`, `left_upper_leg`,
  and `upcomer`.
- Salt blocked thermal branch: `right_leg`.
- Water blocked left-side branch: `left_lower_leg`.
- Water supporting-only branch: `test_section_span`.

Without branch promotion gates, the paper and any downstream model dependency
work would mix scrutiny-cleared effective quantities with denominator-driven or
mask-dominated artifacts.

## How Salt and Water should be compared without overclaiming

Salt and Water should be compared in two stages:

1. Compare support structure first.
   Determine which branches are scrutiny-cleared, which are marginal, and
   which are blocked.
2. Compare effective transport values only inside the shared support envelope.

At the current state of the package stack:

- Salt-only branch thermal dependency work is defensible on the safe subset.
- Water left-side branch thermal dependency work is not ready.
- Cross-family hydraulic dependency work is not ready while the Water
  left_lower_leg contradictions remain excluded.

That is the correct interpretation boundary for the current audit outputs.
