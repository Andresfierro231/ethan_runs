# Water Provisional And Corrected Salt Gate Work Products

Generated: `2026-07-07`

## Contents

- `water_provisional_run_status.csv`: four Water monitor rows copied from the July 6 rerun inventory and labeled provisional.
- `water_provisional_language_audit.csv` / `.json`: audit of Water language in the task report, summary, work-product README, journal, operational note, and import manifest.
- `corrected_salt_preflight_audit.csv` / `.json`: read-only audit from `tools/analyze/check_corrected_salt_preflight.py`.
- `salt_gate_submission_status.csv`: live/canceled/replacement Slurm gate state.

## Admission Boundary

Water is reportable only as provisional monitor evidence from a timeout/frozen final window. The July 6 consolidated closure table did not add Water closure rows.

Corrected Salt preflight passed for all 14 staged corrected Q cases, but the live solver jobs are still running. Corrected Salt remains inadmissible for closure or ROM fitting until the replacement gate job writes `run_status/run_status_inventory.csv` and any row intended for fitting has `operating_point_verdict=requalified`.

The separate live monitor package at `work_products/2026-07-07_corrected_salt_live_monitor/` carries `needs_special_gate_scrutiny` forward. Any flagged row remains inadmissible for closure fitting without coordinator review even if a later formal gate appears to requalify it.
