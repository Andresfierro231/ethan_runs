# Journal — AGENT-244 — 2026-07-09

Date: 2026-07-09
Role: Implementer / Writer
Task: AGENT-244 (originally drafted as AGENT-237, which collided with a completed
Codex task; renumbered)

## Objective

Plot every Ethan CFD run's OpenFOAM postProcessor values vs time (grouped by
quantity), add a last-~5-min companion plot with a linear trendline + equation +
R² in the legend, report RMSE/variance/oscillation with a steady-state verdict,
and compare the mean's uncertainty via CLT / 1-over-sqrt(t). Reusable scripts,
rigorous docs, provenance, data disclosure. Submit an overnight job only if the
run would exceed 30 min.

## Files inspected (READ-ONLY)

- `jadyn_runs/**/postProcessing/` — 52 dirs. Formats confirmed:
  - `mdot_<leg>/<startTime>/surfaceFieldValue.dat` (col `sum(phi)`),
  - `temperature_probes/<startTime>/T` and `wall_temperature_probes/<startTime>/T`
    (`# Probe N (x y z)` header + per-probe columns),
  - `total_Q.dat` (bare `time  Q`).
- `AGENTS.md`, `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`, `.agent/ROLES.md`.

## Files created

- tools/analyze/openfoam_timeseries.py, timeseries_stats.py,
  svg_timeseries_chart.py, build_timeseries_steadystate_report.py
- tools/analyze/test_openfoam_timeseries.py, test_timeseries_stats.py
- work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/** (417 SVGs,
  per-case stats, cross-case summary, README/METHODOLOGY/DATA_DISCLOSURE, summary.json)
- imports/2026-07-09_timeseries_steadystate.json
- .agent/status/2026-07-09_AGENT-244.md

## Commands run

```bash
python tools/analyze/build_timeseries_steadystate_report.py --limit 2 --output-dir <tmp>   # smoke
python -m pytest tools/analyze/test_openfoam_timeseries.py tools/analyze/test_timeseries_stats.py -q  # 19 pass
python tools/analyze/build_timeseries_steadystate_report.py   # full: 47 cases, ~2m32s
convert -density 100 <svg> <png>   # visual verification of layout
```

## Results / observations

- 52 postProcessing dirs; 5 byte-identical duplicates (failed_stage_preserved +
  staging mirrors) detected by fingerprint and excluded → 47 unique cases.
- Time is in seconds (t_end ~2400–11700 s); window = last 300 s.
- Verdicts by group (representative rows): mdot 40/5/2, temperature 275/1/0,
  wall_temperature 46/0/0, heat 6/5/35 (steady/quasi/not-steady).
- mdot last-300s clearly resolves a periodic oscillation (~0.01–0.2% of the mean)
  with a small drift; corrected relative SEM (autocorrelation-adjusted) is
  ~0.001–0.05% of the mean for mainline Salt.
- SEM-vs-averaging-time tracks the 1/√t CLT reference on log-log.

## Rigor decisions / bugs fixed

- **Near-zero-mean trap.** First cut divided drift by the mean; `total_Q` is the
  NET heat residual (~0.1 W) so relative drift exploded and falsely read
  "not steady". Fixed: use relative-to-mean drift only when
  `|mean| > 3·std`, else a scale-free `drift_ratio = |trend change|/oscillation
  amplitude`. Added `drift_ratio` + `near_zero_mean` columns and a regression test.
  (Intermediate over-correction — applying drift_ratio>3 globally — wrongly
  flagged salt1 heat, mean −9.1 W, drift 1.7%; final logic is the two-branch rule.)
- **Duplicates** excluded by content fingerprint, all listed in `case_inventory.csv`.
- **Autocorrelation-corrected SEM** because CFD samples are correlated; naive
  σ/√N understates uncertainty. Both reported.
- Pure-Python stats + stdlib-only SVG so the package rebuilds in a minimal shell.
- Runtime 2m32s << 30 min → ran locally; no overnight job (per user's threshold).

## Incomplete / not done

- Only scalar time series; field samples (velocity/PIV/wallHeatFlux fields) not
  processed. Per-patch heat accounting lives in the patchwise heat ledger.
- No mesh/GCI (all cases coarse_no_gci). A "steady" verdict = time-series
  stationarity, not operating-point correctness.

## Next steps

- Rerun with `--window-seconds N` to change the averaging window.
- Optional absolute heat-vs-time via per-patch `wallHeatFlux.dat` aggregation.
- The salt3 corrected-Q (hi5q/hi10q) not-steady mdot corroborates the
  corrected-Salt gate; feed into any perturbation requalification.
