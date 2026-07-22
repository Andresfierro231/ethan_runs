# Minor Loss Two-Tap Ledger

Generated: `2026-07-08T14:54:18`
Task: `TODO-MINOR-LOSS-TWO-TAP`

## Scope

This package converts preserved Salt 2/3/4 Jin two-interface feature losses into
a stricter minor-loss table. It is a 3D CFD postprocessing reduction, not a 1D
solver calculation.

## Method

For preserved corner rows, the legacy feature extractor already computed:

```text
P0_proxy = <p_rgh> + 0.5 <rho> |<U>|^2
feature_total_pressure_loss = -(Delta p_rgh + buoyancy_term + Delta q_dyn)
K_apparent = feature_total_pressure_loss / q_ref_local
```

This pass joins each feature to the July 8 pressure ledger, computes an
available adjacent straight-loss estimate, and emits:

```text
local_minor_loss = max(feature_total_pressure_loss - adjacent_straight_loss, 0)
K_local = local_minor_loss / q_ref_local
```

Because the preserved feature rows do not contain full centerline tap-to-tap
length, `adjacent_straight_loss` uses `abs(dz_across_feature_m)` as a minimum
tap-length proxy. Therefore `K_local` remains an upper-bound estimate and is
flagged as such.

## Outputs

- `minor_loss_two_tap.csv`
- `minor_loss_two_tap.json`
- `summary.json`
- `README.md`

## Counts

- rows: `15`
- computed preserved corner rows: `12`
- unavailable expected feature rows: `3`

## Scientific Use

- Use `K_apparent` only as a diagnostic value that reproduces the preserved
  total-pressure feature loss without adjacent straight-loss subtraction.
- Use `K_local` as the current best local minor-loss upper-bound estimate.
- Do not use rows with `recirculation_adjacent` as ordinary single-stream
  closure fits.
- The `test_section_complex` rows are intentionally marked unavailable because
  the preserved July 1 bend-minor-loss output did not include that feature.

## Source Evidence

- Pressure ledger: `work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- Preserved bend/minor rows: `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.csv`

## Reproduce

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python tools/extract/sample_minor_loss_two_tap.py
python -m pytest tools/extract/test_sample_minor_loss_two_tap.py -q
```
