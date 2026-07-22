# Setup/BC/Model-Form Error Synthesis Report

Task: AGENT-424
Generated: 2026-07-15

This package summarizes the different 1D setup variants, boundary conditions,
modeling assumptions/forms, and resulting mass-flow and TP/TW temperature
errors from existing evidence only. It does not launch OpenFOAM, mutate native
CFD outputs, mutate registry/admission state, or edit external Fluid files.

Open `report.md` first.

## Files

- `report.md`: report-ready synthesis.
- `case_setup_summary.csv`: Salt case setup and split table.
- `boundary_model_matrix.csv`: boundary/mode assumptions and predictivity class.
- `mode_error_summary.csv`: mean mdot and all-probe error by mode.
- `case_mode_error_matrix.csv`: per-case mdot/TP/TW/Tmean/loop-dT errors.
- `heater_cooler_model_form_errors.csv`: heat-added/removed model-form errors.
- `setup_predictive_variant_status.csv`: implemented setup-only Fluid hooks.
- `assumptions_and_guardrails.csv`: assumption register with risks.
- `source_manifest.csv`: exact source paths.
- `summary.json`: machine-readable summary.

## Headline Numbers

- M1 full CFD segment heat ledger: 35.874 pct mean
  absolute mdot error, 159.168 K all-probe RMSE.
- M2 CFD heater + test-section net + cooler: 10.397
  pct mean absolute mdot error, 26.972 K all-probe RMSE.
- M3 CFD heater + cooler only: 16.826 pct mean
  absolute mdot error, 18.023 K all-probe RMSE.

## Guardrail

Rows that consume realized CFD wallHeatFlux, imposed CFD cooler duty, or CFD
mdot at runtime are diagnostic. They are not final setup-only predictive model
results.
