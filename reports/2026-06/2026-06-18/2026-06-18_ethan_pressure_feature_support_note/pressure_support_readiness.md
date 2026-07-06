# Pressure Support Readiness

## Feature K_eff

Keep feature `K_eff` at `not_ready`. The current residual closure is still based on stored `p_rgh` feature loss relative to adjacent major-span reference pressure drops. Without a dedicated feature-path density integral, even a clean-looking case trend is not enough to defend direct model fitting.

## Hydro-corrected straight-section pressure rows

Keep the hydro-corrected straight-section rows at `diagnostic_only`. They are useful because they quantify how strongly `p - p_rgh` dominates the raw wall-pressure range, especially in Water, but the remaining straight-section closure residuals are too large to claim closure-quality direct observables.
