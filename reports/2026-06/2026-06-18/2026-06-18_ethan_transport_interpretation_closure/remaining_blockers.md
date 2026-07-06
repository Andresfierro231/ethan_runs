# Remaining Blockers

1. Cross-family hydraulic left_lower_leg dependency remains blocked because both Water rows are excluded from the usable evidence subset.
2. Water left_lower_leg and upcomer thermal metrics remain blocked by small |T_bulk - T_wall| and low usable fraction; these branches are not ready for Water-family HTC, UA', or R'_th dependencies.
3. Salt and Water right_leg effective thermal metrics remain blocked from headline use because the usable fraction stays near the low-support boundary even when the mean driving temperature is not small.
4. Boundary-layer landmarks remain contextual-only; they should not be used as a primary model evidence layer until a future scrutiny pass explicitly upgrades them.
5. Momentum resistance remains a proxy diagnostic and should not be fitted as if it were a directly measured closure quantity.

If a future cross-family hydraulic fit is required, the next follow-up should not be another generic dashboard rebuild. It should either:
- move to a different branch evidence subset that is already scrutiny-cleared, or
- perform a dedicated direct-branch reduction redesign that uses cumulative direct p_rgh drop rather than a weak branch-mean finite-difference average for excluded Water left_lower_leg rows.
