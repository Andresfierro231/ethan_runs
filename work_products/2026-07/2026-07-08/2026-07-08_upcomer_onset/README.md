# Upcomer Onset Regime Table

Generated: `2026-07-08T15:14:33`

## Scope

Starter package for `TODO-UPCOMER-ONSET`. It converts the AGENT-196 upcomer
correlation output into a regime table and figure. It does not admit corrected
Salt perturbation rows and does not claim mesh-qualified onset.

## Observed Facts

- Rows: `3` admitted Salt 2/3/4 mainline points.
- All current points classify as `recirculation_cell_observed`.
- Backflow fraction decreases with Re across the admitted range, but remains
  nonzero at Salt 4.
- Route A onset midpoint from AGENT-196 is `250`; Route B midpoint is `167.5`.

## Inferred Interpretation

The upcomer is currently a mixed-convection recirculation-cell problem rather
than an ordinary pipe-friction span. Onset thresholds are still extrapolated
because all admitted points are inside the recirculating regime.

## Blockers

- Only three admitted operating points.
- No mesh/GCI uncertainty.
- Corrected Salt perturbation conclusions remain work in progress and are not
  used here.
- Wall-core Delta T is not yet directly available in the regime table source.

## Recommended Next Action

Use `figures/upcomer_onset_regime.svg` as a regime-table figure, with caveats.
Add new CFD/design points near Re 150, 200, and 250 before fitting a threshold.
