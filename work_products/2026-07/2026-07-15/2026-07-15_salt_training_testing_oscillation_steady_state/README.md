# Salt Training/Testing Oscillation and Steady-State Report

Task: AGENT-411
Generated: 2026-07-15
Last-window definition: final `300 s` of each available postProcessing time series.

## Scope

This package analyzes the current Salt thermal training/testing rows from
`2026-07-15_salt_forward_v1_unblock/salt_training_fit_input_table.csv`: Salt1 nominal
and +/-10Q, Salt4 nominal and +/-5Q, and Salt2 +/-5Q holdout/testing rows. It also
cites the canonical forward-v1 ledger, where the setup-legal HX candidate lane still
uses Salt2 train, Salt3 validation, and Salt4 holdout. Those are distinct split policies;
this report does not change admission or fitting status.

## Math and Assumptions

- TP is `postProcessing/temperature_probes/*/T`; TW is
  `postProcessing/wall_temperature_probes/*/T`; mdot is
  `postProcessing/mdot_pipeleg_*/surfaceFieldValue.dat` `sum(phi)` in kg/s.
- Oscillation RMS is `sqrt(mean((x_i - mean(x))^2))` over the last window.
- Oscillation variance is `mean((x_i - mean(x))^2)` over the last window.
- A linear trend `x = a t + b` is also fit over the last window; drift ratio is
  `|a| * window_seconds / RMS_about_trend`.
- Independent-sample CLT uncertainty of a time average is `SEM = sigma/sqrt(N)`.
- CFD samples are autocorrelated, so the report also gives
  `SEM_corrected = sigma/sqrt(N_eff)` with `N_eff = N/tau_int`.
- The 1/sqrt(t) curves are diagnostic convergence plots, not proof of independence.

## Results

- Selected cases resolved: `8`.
- Series/stat rows written: `456`.
- SVG figures written: `96`.

Representative case-level verdicts:

| case | split role | steady reps | quasi reps | drifting reps | verdicts |
| --- | --- | ---: | ---: | ---: | --- |
| salt1_hi10q | training_perturbation | 3 | 0 | 0 | steady |
| salt1_lo10q | training_perturbation | 3 | 0 | 0 | steady |
| salt1_nominal | training | 3 | 0 | 0 | steady |
| salt2_hi5q | holdout_perturbation | 3 | 0 | 0 | steady |
| salt2_lo5q | holdout_perturbation | 3 | 0 | 0 | steady |
| salt4_hi5q | training_perturbation | 3 | 0 | 0 | steady |
| salt4_lo5q | training_perturbation | 3 | 0 | 0 | steady |
| salt4_nominal | training | 3 | 0 | 0 | steady |

Representative last-window oscillation metrics:

| case | TP RMS K | TP var K^2 | TW RMS K | TW var K^2 | mdot RMS kg/s | mdot var (kg/s)^2 | max corrected relative SEM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| salt1_hi10q | 1.932676241e-12 | 3.735237454e-24 | 6.252776075e-13 | 3.909720864e-25 | 7.628961355e-09 | 5.820105135e-17 | 3.767531178e-08 |
| salt1_lo10q | 2.330580173e-12 | 5.431603944e-24 | 6.252776075e-13 | 3.909720864e-25 | 2.882979882e-09 | 8.311573e-18 | 2.733180685e-08 |
| salt1_nominal | 1.250555215e-12 | 1.563888346e-24 | 1.648459147e-12 | 2.717417559e-24 | 4.338587903e-10 | 1.882334499e-19 | 2.226919393e-09 |
| salt2_hi5q | 0.0821792756 | 0.006753433339 | 0.0759951463 | 0.005775262262 | 7.542426415e-06 | 5.688819623e-11 | 6.916363251e-05 |
| salt2_lo5q | 0.0683177958 | 0.004667321223 | 0.06360666554 | 0.004045807901 | 6.260545733e-06 | 3.919443288e-11 | 6.334523564e-05 |
| salt4_hi5q | 0.1349878372 | 0.01822171619 | 0.109503765 | 0.01199107454 | 4.508049475e-05 | 2.032251007e-09 | 0.0006341583386 |
| salt4_lo5q | 0.1053351215 | 0.01109548781 | 0.1006207763 | 0.01012454062 | 3.154827082e-05 | 9.952933917e-10 | 0.0004748105198 |
| salt4_nominal | 0.05124919939 | 0.002626480438 | 0.03389666741 | 0.001148984061 | 3.829470404e-05 | 1.466484358e-09 | 0.0005247165452 |

Steady-state reading: all individual and representative TP/TW/mdot series in this
selected set are `steady` by the documented thresholds in the final 300 s. Some
Salt2/Salt4 perturbation representatives have large drift-ratio values because the
detrended RMS is very small; their physical drift over the window remains below
`0.24%` of the mean in this run.

## Files

- `selected_cases.csv`: resolved Salt training/testing rows and postProcessing paths.
- `oscillation_stats.csv`: per-series TP/TW/mdot last-window RMS, variance, drift, SEM, and verdicts.
- `case_summary.csv`: representative TP/TW/mdot verdict summary by case.
- `representative_metrics.csv`: compact per-case TP/TW/mdot RMS, variance, SEM, and verdicts.
- `figure_manifest.csv`: generated SVG plot inventory.
- `figures/*.svg`: full traces, last-window traces, mean-fluctuation traces, and CLT SEM curves.
- `source_manifest.csv`: provenance inputs.

## Interpretation Guardrail

These plots quantify whether the consumed time windows are steady enough for reporting.
They do not make single-stream Nu/f_D/K labels valid in recirculating regimes and do not
admit final forward-v1 closure evidence.
