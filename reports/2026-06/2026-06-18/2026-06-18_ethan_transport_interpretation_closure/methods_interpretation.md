# Methods Interpretation

## Scope

This closure note tightens the June 18 scientific interpretation package after
one bounded forensic audit of Water 2 left_lower_leg. It does not redefine the
implemented transport formulas. It explains how the existing reductions should
be read after the final direct-versus-shear hydraulic audit on the last active
Water branch contradiction.

## What the effective hydraulic quantities mean

The shear-based hydraulic reduction is a wall-stress reduction. It projects
wall shear onto the repaired streamwise tangent, area-averages the projected
streamwise magnitude, and then converts that wall-stress surrogate into
Darcy/Fanning form with the current hydraulic-diameter and bulk-speed
surrogates. It is therefore a wall-stress-derived hydraulic indicator, not a
direct measurement of branchwise control-volume pressure drop.

The direct hydraulic reduction is a wall-registered pressure diagnostic. It
area-averages wall `p_rgh` in each streamwise bin, finite-differences those
wall means along the repaired coordinate, and converts the result into
Darcy/Fanning form with the same surrogate geometry. It is a wall-pressure
indicator, not a momentum-balance closure.

## Why direct and shear hydraulic reductions may disagree

Direct and shear reductions can disagree because they use different
observables, different numerical conditioning, and different failure modes.
The direct `p_rgh` path is especially vulnerable when the net branch signal is
small: mixed positive and negative local derivatives can average toward zero
or change sign even when the branch-end cumulative direct drop remains
positive.

The Water left_lower_leg rows show the two important cases:

- Water 1 left_lower_leg: Treat the contradiction as a resolved exclusion rather than a usable hydraulic dependency. The direct p_rgh signal is about one order of magnitude smaller than the shear-implied branch drop (terminal ratio 0.104), and the mean direct gradient is effectively a weak-signal average over mixed-sign local derivatives.
- Water 2 left_lower_leg: Resolved exclusion. Water 2 left_lower_leg does not show evidence of a stable branchwise pressure-drop reversal. All retained times keep a positive branch-end cumulative direct p_rgh drop, one retained time carries a unique alignment-sign flip relative to the modal branch orientation, and the remaining sign changes in the branch-mean direct gradient are weak-signal finite-difference cancellations rather than robust reversals.

The Water 2 closure audit tightened one important distinction. The branch is
still excluded from model dependency work, but it no longer needs to remain
labelled unresolved at the sign-mystery level. The direct branch-end cumulative
drop stays positive in every retained time; the problem is that one retained
time carries the only non-modal alignment sign while the remaining branch-mean
sign changes are weak-signal differencing cancellations.

## Why disagreement in pressure-drop direction is a stop condition

If direct and shear reductions disagree at the sign level, the reduced branch
result is not robust enough to serve as cross-family evidence. Even if the row
is later resolved as an exclusion rather than an open mystery, it still cannot
be used as hydraulic model evidence for that branch.

## Why branch-end cumulative direct drop and branch-mean direct gradient can diverge

These two direct diagnostics are not redundant:

- The branch-end cumulative direct drop preserves the net direct `p_rgh`
  change accumulated along the branch.
- The branch-mean direct gradient averages local finite-difference derivatives
  that can change sign bin-by-bin.

When the net direct signal is weak, the cumulative branch-end drop can remain
positive while the branch-mean local direct gradient oscillates around zero or
changes sign. That is exactly why the Water rows are excluded rather than
reinterpreted as real branchwise pressure recovery.

## Why effective HTC, UA', and R'_th remain support-gated

The effective thermal quantities are ratios:

- `h_eff = |q''_w| / |T_bulk - T_wall|`
- `UA'_eff = |q'_w| / |T_bulk - T_wall|`
- `R'_th = 1 / UA'_eff`

They become unstable when the resolved branch-scale driving temperature
collapses. A large reported effective HTC or a numerically smooth `R'_th` is
not enough to promote a branch. The usable fraction, warning fraction, and
minimum resolved `|T_bulk - T_wall|` still control whether the quantity is fit
eligible or only diagnostic.

## Why momentum resistance remains proxy-only

Momentum resistance is local `dp/ds` divided by `mdot`. It is useful for
internal comparison, but it inherits the same branch exclusions and hydraulic
conditioning limits as the underlying direct or shear gradient. It is therefore
not a directly measured closure-quality resistance law.

## Why branch promotion gates remain necessary

The closure pass does not widen the thermal trust boundary. The Salt safe
subset remains:

- `left_lower_leg`
- `test_section_span`
- `left_upper_leg`
- `upcomer`

Blocked branches remain blocked because their support path did not improve:

- Salt and Water `right_leg` remain non-headline thermal branches.
- Water `left_lower_leg` and `upcomer` remain support-limited thermal branches.
- Boundary-layer landmarks remain contextual-only.

## How Salt and Water should be compared after this closure pass

The correct comparison sequence is now:

1. Compare support structure and branch eligibility first.
2. Compare effective thermal values only inside the shared support envelope.
3. Keep cross-family hydraulic left_lower_leg work blocked because the Water
   evidence for that branch is excluded from the usable subset.

At the current state of the audit stack:

- Salt-only branch thermal dependency work is defensible on the safe subset.
- Water left-side branch thermal dependency work is still not ready.
- Cross-family hydraulic dependency work remains blocked, but now because the
  Water branch is excluded from evidence rather than because an unresolved sign
  mystery remains.
