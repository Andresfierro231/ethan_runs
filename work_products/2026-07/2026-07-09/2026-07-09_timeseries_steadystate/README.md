# Postprocessor Time-Series & Steady-State Analysis — AGENT-244, 2026-07-09

Value-vs-time plots, last-window trend fits, oscillation/RMSE statistics, and a
central-limit-theorem uncertainty analysis for every Ethan CFD run's OpenFOAM
`postProcessing` scalar output (jadyn + modern runs).

## What is here

- `cases/<slug>/figures/` per case:
  - `<group>_timeseries.svg` — full run, grouped (mdot legs / temperature probes /
    wall-temperature probes / total_Q).
  - `<group>_last300s.svg` — last 300 s with a linear
    trendline, its **equation and R² in the legend**.
  - `mdot_sem_convergence.svg` — standard error of the mean vs averaging time
    with the **1/√t CLT reference**.
- `cases/<slug>/stats.csv` + `stats.json` — every series' full statistics.
- `steady_state_summary.csv` — one representative row per case/group: verdict,
  mean, RMSE (about mean and about trend), variance, CoV, trend slope/R²,
  autocorrelation time, effective N, SEM (naive + corrected), relative SEM.
- `case_inventory.csv` — all 52 postProcessing dirs with content
  fingerprints and duplicate flags (5 byte-identical duplicates excluded
  from analysis).
- `METHODOLOGY.md` — exact definitions of every statistic and the steady-state
  criteria. `DATA_DISCLOSURE.md` — inputs, units, sign conventions, exclusions.

## Coverage

- 47 unique cases (of 52 postProcessing dirs); fluids: salt1, salt2, salt3, salt4, water1, water2, water3, water4.
- Window = last 300 s of simulated time ("last ~5 minutes").

## Headline (representative series, last-window verdict)

Overall: 367 steady · 11 quasi-steady · 37 not steady.

By quantity group:
  - **mdot**: 40 steady, 5 quasi-steady, 2 not steady
  - **temperature**: 275 steady, 1 quasi-steady, 0 not steady
  - **wall_temperature**: 46 steady, 0 quasi-steady, 0 not steady
  - **heat**: 6 steady, 5 quasi-steady, 35 not steady

**Read this correctly.** The mass flow and temperatures are steady in almost
every case — the loops reach a stationary (often gently oscillating) state. The
"not steady" rows are dominated by the `heat` group, which is `total_Q`, the
**net heat residual** (heat in − out). That residual is ≈ 0 at steady state
(order 0.1 W against a loop heat scale of hundreds of W), so a small absolute
drift is a large *relative* drift — the verdict flags the residual's noisiness,
not a genuine thermal runaway. The only `mdot` rows flagged not-steady are the
salt3 corrected-Q perturbations (hi5q/hi10q), whose mass flow is still moving —
consistent with the corrected-Salt gate marking them "too short / needs extended
continuation."

See `steady_state_summary.csv` for the numbers behind each verdict (mean,
`drift_ratio`, `rel_drift_over_window`, `near_zero_mean`). Verdicts are advisory
and use the explicit thresholds in `METHODOLOGY.md`.

## Caveats

- All admitted CFD is `coarse_no_gci`; these are convergence/steadiness
  diagnostics, not mesh-converged results.
- The June Q-perturbation runs were previously flagged "false-steady" (mdot never
  moved). A "steady" verdict here means the *time series* is stationary; it does
  **not** certify the operating point is physically correct. Cross-check the
  corrected-Salt gate before using any perturbation row as evidence.
- `mdot` is `sum(phi)` through an oriented faceZone (kg/s for this compressible
  buoyant solver); by mass continuity all legs carry the same loop mdot, so the
  heater leg is the representative for trend/CLT.

## Reproduce

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python tools/analyze/build_timeseries_steadystate_report.py --window-seconds 300
python -m pytest tools/analyze/test_openfoam_timeseries.py tools/analyze/test_timeseries_stats.py -q
```
