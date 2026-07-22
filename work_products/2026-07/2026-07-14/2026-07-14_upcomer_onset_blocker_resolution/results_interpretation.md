# Results Interpretation

## Observed Facts

- Current admitted onset dataset has `3` rows.
- Re range is `71.125` to `134.883`.
- All rows classify as `recirculation_cell_observed`.
- Minimum current backflow fraction is `0.171875`.
- Minimum current `Ri_median` is `1.497987`.
- Route A midpoint Re `250.0` is `115.117` above current Re max.
- Route B midpoint Re `167.5` is `32.617` above current Re max.

## Inferred Interpretation

The current evidence supports a strong diagnostic claim: the admitted Salt2/3/4
upcomer rows are mixed-convection recirculation-cell rows and should not be
named as ordinary single-stream `f_D`, `K`, or `Nu` closures. The evidence does
not support a calibrated onset threshold because there is no non-recirculating
anchor, no dense transition bracket, and no mesh/time uncertainty bound for the
onset metrics.

## Thesis-Safe Claim

For the admitted Salt2/3/4 points, the upcomer is observed in a recirculating
mixed-convection regime. The onset location is bracketed only by extrapolation
from the current three-point trend and should be treated as an experimental or
CFD-design target, not a closure.

## Excluded Claims

- A calibrated recirculation onset Reynolds number.
- A production regime switch for the 1D model.
- A universal upcomer `f_D`, `K`, or `Nu` value across the recirculating region.
- Any claim that corrected Salt-Q resolves onset before terminal admission.
