# Registry corrected-Q status table

Task: AGENT-250

## Observed

- `registry/case_registry.csv` had only the original 14 data rows and no corrected-Q perturbation case roots.
- `corrected_case_manifest.csv` has 14 corrected-Q perturbation rows.
- The completed gate `3280969` and minimal continuation plan already contain the status/time fields needed for the compact table.

## Actions

- Appended all 14 corrected-Q perturbation case roots to `registry/case_registry.csv` with `source_owner=corrected_salt_q_sensitivity`.
- Added a reusable table builder that uses registry rows as the case set and joins gate/recommendation evidence.
- Wrote selected three-row and all-corrected tables plus a registry coverage CSV.

## Validation

- `python3.11 -m unittest tools.analyze.test_registry_corrected_q_status_table`
- `python3.11 tools/analyze/build_registry_corrected_q_status_table.py --strict-registry`
- `python3.11 -m json.tool imports/2026-07-10_registry_corrected_q_status_table.json`

## Interpretation

The table is now reproducible from registry-backed case identity plus gate evidence. The corrected-Q registry entries are provenance registrations only and do not change admission status.
