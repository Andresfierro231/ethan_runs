# Ethan Runs Update

Date: 2026-06-07

## Observed Outputs

- Standardized the local figure convention on typed subfolders: `figures/png/`, `figures/svg/`, and `figures/pdf/`.
- Added shared figure-bundle helpers in `tools/common.py` and refreshed the report builders so regenerated outputs now land in typed figure subfolders for:
  - `reports/2026-06-05_ethan_continuation_diagnosis/`
  - `reports/2026-06-05_ethan_convergence_and_salt1_campaign/`
  - `reports/2026-06-05_ethan_wall_loss_resistance_coupling/`
  - `reports/2026-06-04_salt2_behavior_package/`
  - `reports/2026-06-04_ethan_transient_axial_package/`
  - `reports/2026-06-01_weekly_status/`
- Removed stale root-level PNG duplicates from `reports/2026-06-04_ethan_transient_axial_package/` so the typed figure folders are now the only figure outputs there.
- Patched `tools/extract/render_last_timestep_temperature_slices.py` so the ParaView slice plane now uses the reference `z` plane rather than the old `x=0` plane:
  - `slice_origin = [xmid, ymid, z_reference]`
  - `slice_normal = [0, 0, 1]`
  - camera offset is now along `-z`
- Fixed two renderer implementation issues that were exposed during the convention change:
  - typed outputs now write directly into `figures/png|svg|pdf` instead of `figures/figures/...`
  - status JSON now serializes camera vectors as plain float lists, which removed the previous post-render ParaView failure.
- Re-ran verified compute-node smoke renders for two registered cases under the new `z`-reference convention:
  - `3214869`: `viscosity_screening_salt_test_1_kirst_coarse_mesh` completed and wrote PNG/SVG/PDF under `figures/`
  - `3214870`: `val_salt_test_2_coarse_mesh_laminar` completed and wrote PNG/SVG/PDF under `figures/`
- Wrote updated aggregate render status at `figures/last_timestep_temperature_slice_status.json` and removed the obsolete flat root-level PNG/SVG slice files.
- Refreshed the June 5 continuation diagnosis so the current recorded sequence now includes the later repaired-runtime outcomes:
  - `3202708`: Salt 2 continuation timed out on 2026-06-07
  - `3210231`: Salt 4 Jin repaired continuation still running on 2026-06-07 at the time of refresh
  - `3210268`, `3210761`, `3211197`: Salt 1 Jin repaired retries completed successfully
  - `3210760`: Salt 1 Kirst repaired retry completed successfully
  - `3211199`: Salt 1 Kirst follow-on retry failed on missing root-level `T`
- A fresh run attempt for the transient/axial base package still hit the pre-existing reconstructed-`T` readability failure on some cases, with `foamPostProcess` reporting a scalar-token parse error rather than a new figure-layout problem.

## Interpretation

- The figure-export convention is now consistent across the refreshed local report packages and the ParaView slice workflow: raster, vector, and LaTeX-friendly PDF outputs are separated by type instead of mixed into a single folder.
- The last-timestep temperature slice workflow is now aligned with the intended physical frame: it is a reference-`z` slice with a `-z` viewing direction, and that path is verified on actual compute-node renders rather than only by code inspection.
- The repaired continuation bootstrap path is no longer the main Salt 1 question. Salt 1 Jin has multiple successful repaired retries, and Salt 1 Kirst has one successful repaired retry plus one later staging-tree failure that is specific to the restart field layout.
- The main unresolved technical blocker in the reporting stack is still reconstructed-`T` readability for some transient axial postprocessing rows, not figure generation itself.

## Contradictions / Caveats

- The ParaView `z`-reference rerender was verified for the two smoke-render cases above, not yet for every registered case in the inventory.
- The current verified slice outputs are represented by `figures/smoke_kirst_status.json`, `figures/smoke_salt2_status.json`, and the aggregate `figures/last_timestep_temperature_slice_status.json`.
- Salt 4 Jin `3210231` was still live when the continuation diagnosis was regenerated. Any later runtime change after this journal entry needs a follow-on update rather than being silently assumed here.
- No new case source was imported today, so `registry/case_registry.csv` was referenced but not expanded with a new row.

## Suggested Next Actions

- Fan out the repaired `z`-reference ParaView render path to the remaining registered cases using one job per case, then update the aggregate status JSON once the full batch exists.
- Repair the Salt 1 Kirst staged restart tree before any retry after `3211199`, because that failure is a missing root-level `T` problem rather than an MPI/bootstrap problem.
- Decide whether Salt 2 is worth another continuation extension now that `3202708` has timed out rather than failed environmentally.
- Keep monitoring Salt 4 Jin `3210231` until it reaches either a defensible runtime checkpoint or a new failure mode.
- Make the reconstructed-`T` read path uniform enough for `foamPostProcess` so the transient axial package can be rebuilt cleanly without q-only fallbacks.
## Additional candidate figures and simulations

### Observed candidate outputs

- Full registered-case rollout of the repaired `z`-reference last-timestep temperature slices, not just the two smoke-render cases.
- Geometric-arc-length axial figures for wall temperature, Nusselt number, and wall heat flux, replacing the current patch-progress x-axis where manuscript quality requires a physical length coordinate.
- Late-time section `Delta p_rgh` evolution figures for the upper leg, left leg, and test-section branch so the resistance argument can be shown as a transient rather than only as a latest-time ranking.
- Jin-vs-Kirst delta figures at matched salt test number, especially for mass flow, upper-leg pressure drop, and ambient-loss proxy, so the parameter-family differences are shown directly instead of only through separate plots.
- Junction or upper-leg velocity / temperature visualizations from reconstructed latest-time fields, because that region remains the strongest hydraulic sensitivity candidate.
- End-state continuation comparison panels that show pre-repair versus repaired-runtime outcomes for Salt 1, Salt 2, and Salt 4 on one timeline.

### Interpreted simulation candidates

- A Salt 2 continuation extension remains scientifically defensible if more late-time steadiness evidence is still worth the allocation.
- A repaired Salt 1 Kirst continuation retry is still the cleanest next simulation for closing the restart-tree question raised by `3211199`.
- If Salt 4 Jin finishes without a new environment failure, a targeted follow-on sensitivity around upper-leg resistance or ambient loss becomes more valuable than another blind retry.
- If the manuscript needs a stronger causal test, a small targeted sensitivity set around wall loss and upper-leg resistance is probably more discriminating than broad new parameter sweeps.

### Caveats

- The geometric-arc-length axial figures are not a trivial plot toggle; they need a centerline-aware extraction step rather than reuse of the current ordered patch index.
- Any new simulation request should avoid reopening the already-resolved runtime-bootstrap question unless a genuinely new failure signature appears.
- Additional ParaView field figures should continue to use reconstruction-first staging and one render process per case.

### Suggested next actions

- Pick one figure family first: pressure-evolution, geometric-axial, or Jin-vs-Kirst delta figures.
- Keep the next simulation decision narrow: Salt 2 extension, Salt 1 Kirst repaired retry, or one targeted resistance/loss sensitivity pass.
