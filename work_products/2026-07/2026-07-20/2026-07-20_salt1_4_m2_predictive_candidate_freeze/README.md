# Salt1-4 M2 Predictive Candidate Freeze

Candidate freeze: `M2_CANDIDATE_FREEZE_SALT1_4_NOMINAL_2026_07_20`.

This package starts the first predictive candidate lane from the Salt1-4 nominal row freeze.
It admits only the existing heater and cooler/HX setup boundary terms and keeps pressure, upcomer, PM5, PM10, val_salt2, new-CFD, and two-tap evidence out of fitting/model selection.

Primary outputs:

- `candidate_freeze_manifest.csv`
- `candidate_model_terms.csv`
- `candidate_runtime_input_audit.csv`
- `candidate_fit_provenance.csv`
- `holdout_exclusion_audit.csv`
- `summary.json`

Training rows: 4.
Holdout rows used for fit: 0.
Holdout predictions created: no.
