# TODO-UPCOMER-ONSET Status

Date: `2026-07-08`
Role: Writer / Implementer
Owner: codex

## Scope

Started the upcomer-onset package as a regime-table figure from the completed
AGENT-196 upcomer correlation output.

## Completed

- Added `tools/analyze/build_upcomer_onset_regime_table.py`.
- Added `tools/analyze/test_upcomer_onset_regime_table.py`.
- Generated `work_products/2026-07-08_upcomer_onset/**`.

## Observed Facts

- The package has `3` admitted Salt 2/3/4 mainline rows.
- All three rows classify as `recirculation_cell_observed`.
- Backflow decreases with Re but remains nonzero at Salt 4.
- The package emits `figures/upcomer_onset_regime.svg` and
  `upcomer_onset_regime_table.csv`.

## Interpretation

The upcomer should be treated as a mixed-convection recirculation-cell regime
for the current admitted dataset, not as an ordinary pipe-friction span. The
onset bracket remains extrapolated because no admitted point has yet crossed
into a clean ordinary-pipe regime.

## Blockers

- Only three admitted operating points.
- No mesh/GCI uncertainty.
- Corrected Salt perturbation conclusions remain work in progress and excluded.
- Wall-core Delta T is not directly available in the source table.

## Validation

- `python tools/analyze/build_upcomer_onset_regime_table.py`: passed.
- `python -m pytest tools/analyze/test_upcomer_onset_regime_table.py`: passed,
  `2 passed`.

## Recommended Next Action

Use the figure as a regime-table visualization with caveats. Add admitted CFD
points near Re 150, 200, and 250 plus wall-core Delta T extraction before
fitting an onset threshold.

## Status

STARTED / STARTER PACKAGE COMPLETE.
