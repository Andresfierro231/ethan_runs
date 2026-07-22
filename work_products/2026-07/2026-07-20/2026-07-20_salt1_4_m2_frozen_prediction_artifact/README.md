# Salt1-4 M2 Frozen Prediction Artifact

Frozen model id: `M2_FROZEN_PREDICTION_ARTIFACT_SALT1_4_NOMINAL_2026_07_20`.

This package freezes the M2 admitted heater/cooler boundary artifact for Salt1-4 nominal rows only.
It does not score PM5, PM10, val_salt2, or new-CFD rows.

Primary outputs:

- `candidate_model_freeze.json`
- `train_row_predictions.csv`
- `freeze_runtime_audit.csv`
- `summary.json`

Train rows: 4.
Rows with full admitted boundary predictions: 3.
Holdout rows scored: 0.
