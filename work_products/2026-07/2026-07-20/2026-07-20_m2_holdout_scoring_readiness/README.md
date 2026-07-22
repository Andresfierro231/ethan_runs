# M2 Holdout Scoring Readiness

This package builds the future blind-scoring queue for the M2 artifact.
It does not score PM5, PM10, val_salt2, or new-CFD rows.

Primary outputs:

- `scoring_row_queue.csv`
- `prediction_join_contract.csv`
- `target_leakage_audit.csv`
- `blocked_score_rows.csv`
- `summary.json`

Queue rows: 8.
Rows scored now: 0.
