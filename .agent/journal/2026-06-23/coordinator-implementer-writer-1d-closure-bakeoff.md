# AGENT-114 Raw Journal

Date: `2026-06-23`
Role: `Coordinator / Implementer / Writer`

## Observed output

- The frozen-state validator was still hardwired to `reports/2026-06-22_ethan_frozen_state_results/one_d_readable_status.csv`.
- The only readable Salt diagnostics bundle on disk remains `ethan_cfd_informed_salt_v1`; there is no newer `v2` or retuned Salt diagnostics tree to score locally.
- The staged bakeoff package now publishes:
  - `baseline_full_surface/**`: all `15` readable Salt rows across `6` scenarios
  - `defended_full_coverage_surface/**`: the one full-coverage scenario that stayed accepted across Salt `1-4`, namely `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`
- `surface_summary.csv` shows the same best primary scenario on both surfaces:
  - mean |energy| `11.2743%` heater
  - mean TW RMSE `62.7865 K`
  - mean TP RMSE `62.6925 K`
  - mean mass-flow error `26.6910%`

## Inferred interpretation

- The defended local retune is a scoring/filtering retune, not a physics refresh.
- The main value of the defended surface is that it strips out under-covered hybrid rows and leaves one scenario family that remains readable across all four Salt references.
- Because the best defended scenario is identical to the baseline best primary scenario, the current bottleneck is not scenario selection inside the old readable bundle. The bottleneck is the absence of a genuinely refreshed 1D diagnostics run.

## Contradictions or caveats

- `reports/2026-06-23_ethan_1d_closure_bakeoff/**` already contained extra files with `2026-06-23 11:29` modification times before this pass finished. They were not emitted by `build_ethan_1d_closure_bakeoff.py`.
- I did not delete or rewrite those extra files because that would risk clobbering another Codex pass. The new driver only guarantees the files it explicitly writes: `README.md`, `summary.json`, `surface_summary.csv`, `scenario_shadow_summary.csv`, `baseline_shadow_status.csv`, `defended_shadow_status.csv`, and the two rebuilt surface subdirectories.

## Next suggested actions

- If a refreshed Salt 1D bundle lands externally, rerun `build_ethan_1d_closure_bakeoff.py` against a new shadow status table rather than editing the June 22 validator again.
- If the preexisting `11:29` bakeoff files belong to another active agent, decide later whether to merge them into the current top-level README or quarantine them into a separate dated package.

