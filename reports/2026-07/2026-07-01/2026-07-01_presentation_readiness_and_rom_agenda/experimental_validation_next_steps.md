# Experimental Validation Next Steps

Date: `2026-07-01`

The current 1D ROM evidence is CFD-replay evidence. That is useful for mechanism
identification and post-processing QA, but it is not yet proof that the model is
predictive in the physical experiment.

## Required Data Contract

- Experimental mass flow with uncertainty and calibration history.
- Heater power, wall heat loss, ambient temperature, insulation state, and their
  uncertainties.
- Wall and fluid temperature sensor locations mapped to CFD/1D stations.
- Loop geometry, pipe IDs, bend/fitting definitions, and material/insulation
  properties as installed.
- Run windows that are demonstrably steady or assigned transient uncertainty.

## Validation Protocol

1. Freeze a model form and coefficient set before looking at held-out experiments.
2. Run the 1D model with the experimental boundary conditions and geometry.
3. Compare mass flow, heat balance, wall/fluid temperatures, and pressure-drop
   proxies where available.
4. Quantify error with signed bias, MAE/RMSE, normalized error, and uncertainty
   intervals, not only best-case plots.
5. Calibrate only on a declared calibration subset; report held-out validation
   separately.

## Current Credibility Boundary

Until this is done, the honest claim is: the ROM is being made consistent with
CFD-derived closure physics and post-processing provenance. It is not yet
experiment-validated as a real-world predictor.
