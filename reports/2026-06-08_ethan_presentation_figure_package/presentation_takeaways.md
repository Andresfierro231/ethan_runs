# Ethan Presentation Takeaways

Generated: `2026-06-08T13:46:21-05:00`

## Core message

- `Salt 2` remains the best-supported validation anchor. It is still the clearest sponsor-facing case for saying the 3D workflow is directionally right but still overpredicts `|mdot|` error and underpredicts ambient-like loss.
- `Salt 3 Jin` and `Salt 4 Jin` are usable sensitivity-style steady cases. They support the mechanism story even though `Salt 4 Jin` does not yet have the same validation pedigree as `Salt 2`.
- `Salt 1` still should not be sold as a steady-state success. It remains the weakest family scientifically, and the Kirst retry path is still operationally broken by restart-tree staging.

## Figure-by-figure speaking notes

### `representative_branch_pressure_drop`

- For the current representative usable rows, the upper leg is the dominant hydraulic-loss branch in every case.
- Latest-time `|Delta p_rgh|` in the upper leg is about `36.75 Pa` for `Salt 2 val`, `38.02 Pa` for `Salt 3 Jin`, and `38.43 Pa` for `Salt 4 Jin`.
- The left leg is the second tier at about `15.2-15.5 Pa`, and the right leg is the next tier at about `9.6-11.1 Pa`.
- This is the cleanest branch-level evidence that the remaining `mdot` mismatch is not uniformly distributed around the loop.

### `jin_vs_kirst_delta_dashboard`

- For `Salt 2-4`, switching from Kirst to Jin reduces `|mdot|` error by about `5.46`, `5.47`, and `5.50` percentage points respectively.
- The same Jin-versus-Kirst switch only changes ambient-loss proxy by about `-1.20 W`, `+0.03 W`, and `+0.15 W` for `Salt 2-4`.
- Jin also reduces upper-leg `|Delta p_rgh|` relative to Kirst by about `2.77 Pa` in `Salt 2`, `1.88 Pa` in `Salt 3`, and `2.28 Pa` in `Salt 4`.
- The speaking point is that Jin/Kirst differences move hydraulic agreement much more strongly than they move ambient-loss agreement.

### `representative_heat_balance_partition`

- The heater branch is the main positive input, rising from about `244.66 W` in `Salt 2` to `273.29 W` in `Salt 3` and `310.59 W` in `Salt 4`.
- The cooling branch is the main deliberate sink, at about `-136.35 W`, `-150.77 W`, and `-169.23 W`.
- Junction-region losses are the largest parasitic sink, at about `-40.91 W`, `-43.39 W`, and `-48.85 W`.
- Transport-leg losses are also material, becoming more negative from about `-119.21 W` in `Salt 2` to `-151.23 W` in `Salt 4`.

### `late_window_steadiness_dashboard`

- `Salt 2` and `Salt 3 Jin` show small late-window relative drift across flow, temperature, and ambient-loss proxy.
- `Salt 4 Jin` stays acceptable in temperature and ambient proxy, but its net total wall-heat tail remains notably more active than the stronger steady rows.
- `Salt 1` should not be reclassified from this figure alone. Its caution status comes from the broader convergence and restart evidence, not just the tail statistics shown here.

### Individual stamped temperature and velocity slices

- Use the individual stamped slice figures directly rather than a combined panel. That keeps the PDF/SVG outputs sharp and makes the timestep visible on each image.
- `Salt 2 val` is the stronger visual example for a stable presentation slide because it is also the strongest validation-style case.
- `Salt 3 Jin` and `Salt 4 Jin` now have the same sharp individual temperature and velocity slices available, with black scalar-bar text and black timestep stamps at `t = 2514 s` and `t = 2082 s` respectively.
- `Salt 1 Kirst` is useful as a caution contrast, especially if the audience asks what the weaker family looks like in the same plotting workflow.

## June 8, 2026 live status notes

- `3202708` (`Salt 2 continuation`) is `TIMEOUT` after `5-00:00:22`. The final observed solver tail still showed stable progression to about `5939.017142857 s`.
- `3210231` (`Salt 4 Jin continuation retry`) is `TIMEOUT` after `3-00:00:12`. The final observed solver tail still showed stable progression to about `3942.950738916 s`, with low continuity error and Courant near `0.099`.
- `3211199` (`Salt 1 Kirst retry`) is `FAILED` after `00:00:33`. Treat that as a restart-tree / staging defect, not as evidence that the broader repaired runtime path is fundamentally broken.

## Caveats to say out loud

- The branch-pressure figure is latest-time only. It is strong enough for ranking, but it is not yet a transient `Delta p_rgh(t)` history or a distance-resolved `Delta p(x)` reconstruction.
- The reused transient-axial package gives `Nu(x)` and `q''(x)` style plots, not a separately derived `HTC(x)` curve.
- The presentation package reuses the current June 4-8 report stack. It is a synthesis layer, not a full scientific rerun.
- `Salt 4 Jin` changed state during June 8. Earlier notes that described it as still running are stale; the current Slurm state is `TIMEOUT`.
