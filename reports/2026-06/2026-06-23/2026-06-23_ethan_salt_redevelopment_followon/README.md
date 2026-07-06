# Ethan Salt Redevelopment Follow-On

Generated: `2026-06-23T11:32:26-05:00`

## Scope

- This package keeps the straight-leg story and the bends/corners story separate but adjacent.
- Straight-leg outputs come from preserved `major_loss_cumulative_timeseries.csv` rows for all Salt cases.
- Minor-loss outputs are reused from the June 22 endpoint-path feature decomposition, which already defends patch-endpoint `p_rgh` and `p-p_rgh` across the preserved feature boundaries.

## Current evidence state

- Salt cases plotted here: `9`.
- Straight-leg span summaries published here: `54`.
- Feature-path case rows available from the retained endpoint-path package: `45`.
- Feature-path fit-ready rows currently available: `21`.
- Largest current feature exclusion bucket: `nonpositive_path_feature_excess_loss` with `24` rows.

## Interpretation boundary

- `p_rgh(s)` is hydrostatic-corrected pressure, so it tracks the non-hydrostatic pressure field that remains after the static column is removed.
- `q_dyn(s)` is a kinetic-energy scale, not a pressure field. Overlaying it with `p_rgh(s)` shows whether local acceleration or redevelopment is large enough to matter on the same branchwise order of magnitude.
- `q'(s)` is the streamwise wall heat loss per length. When `q'(s)` stays large, fully developed assumptions stay weak because both the thermal and hydraulic states keep evolving along the same leg.
- The bend/corner lane is now strong enough for endpoint-path feature screening, but it is still not a continuous field-integrated density path. That remains the main remaining minor-loss limitation.
