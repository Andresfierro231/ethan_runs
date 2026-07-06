# Remaining Blockers

1. Water 1 left_lower_leg hydraulic branch remains excluded from model evidence because the mean direct p_rgh gradient is a weak-signal oscillatory average even though the branch-end cumulative p_rgh drop stays positive.
2. Water 2 left_lower_leg hydraulic branch remains unresolved for model use because mixed flow-alignment signs appear inside one retained window while the direct p_rgh signal is weak.
3. Water left_lower_leg and upcomer thermal metrics remain blocked by small |T_bulk - T_wall| and low usable fraction; these branches are not ready for Water-family HTC, UA', or R'_th dependencies.
4. Salt and Water right_leg effective thermal metrics remain blocked from headline use because the usable fraction stays near the low-support boundary even when the mean driving temperature is not small.
5. Boundary-layer landmarks remain contextual-only; they should not be used as a primary model evidence layer until a future scrutiny pass explicitly upgrades them.
6. Momentum resistance remains a proxy diagnostic and should not be fitted as if it were a directly measured closure quantity.

If a future cross-family hydraulic fit is required, the first follow-up should be a bounded audit of the direct branch sign path on Water left_lower_leg using branch-end cumulative p_rgh drop, per-time flow-alignment signs, and any summary aggregation that collapses them into one branch mean.

Current unresolved-exclude rows:
- Water 2 / left_lower_leg: Mixed flow-alignment registration inside one retained time, combined with a weak wall-registered p_rgh signal. The direct cumulative p_rgh drop remains positive for every retained time, but one time window carries flow_alignment_sign = -1 over multiple valid bins, which contaminates the branch-mean direct reduction.
