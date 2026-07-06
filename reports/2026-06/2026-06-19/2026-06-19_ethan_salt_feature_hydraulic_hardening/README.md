# Ethan Salt Feature Hydraulic Hardening

Generated: `2026-06-19`

## Purpose

This package upgrades the Salt feature-loss story beyond the residual-only June
18 audit by recomputing case-level feature excess loss from preserved patch
`p_rgh` endpoint deltas plus a local adjacent-straight reference built from the
nearest valid major-span boundary bins. It does **not** claim a full feature-path
hydro integral; that remains the explicit next upstream requirement.

## Inputs

- `tmp/2026-06-15_live_case_analysis/**/feature_minor_loss_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_cumulative_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_summary.csv`
- `reports/2026-06-18_ethan_salt_closure_correlation_package/salt_feature_correlation_inputs.csv`

## Output tables

- `feature_hydro_closure_timeseries.csv`
  One retained-time feature row with raw patch `p`/`p_rgh` deltas, local
  side-reference gradients, local straight-reference loss, effective `K_eff`,
  and support diagnostics.
- `feature_hydro_closure_by_case.csv`
  One case-level feature row used for downstream feature-fit gating.
- `feature_fit_ready_rows.csv`
  Case-level feature rows that survive the local-support and positive-excess
  gates.
- `feature_exclusion_summary.csv`
  Counted case-level exclusions by primary reason.
- `feature_method_comparison.csv`
  Old span-mean reference versus new local-boundary reference comparison.

## Method status

- Local pressure-loss basis: `abs(delta_p_rgh_pa)` across feature endpoint patches
- Straight-reference basis: half-feature-length times the mean of the nearest
  valid boundary-bin gradients on the start and end adjacent spans
- Deferred upstream term: explicit feature-path hydro-integral sampling

## Key counts

- case count: `9`
- time row count: `185`
- case row count: `45`
- fit-ready feature rows: `21`

## Known limitations

- The new method is stronger than the residual-only June 18 feature budget, but
  it still uses patch-endpoint `p_rgh` plus local straight references rather
  than an explicit feature-path density integral.
- Positive case-level feature excess does not automatically imply a final
  publishable `K_eff`; the downstream dependency package still rechecks
  feature-class stability and sensitivity.
