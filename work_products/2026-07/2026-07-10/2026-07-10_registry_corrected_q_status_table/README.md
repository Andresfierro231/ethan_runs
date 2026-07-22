# Registry corrected-Q status table

Date: `2026-07-10`

## Purpose

Create the compact corrected Salt Q status table from registry case rows instead of manual ad hoc text.

## Outputs

- `selected_corrected_q_status_table.md` and `.csv`: the three-row table for Salt1 -10Q, Salt1 +10Q, and Salt4 +10Q.
- `all_corrected_q_status_table.md` and `.csv`: all registered corrected-Q perturbation rows.
- `corrected_q_registry_coverage.csv`: coverage check against `corrected_case_manifest.csv`; all 14 corrected-Q manifest rows are registered and have matching `source_root` paths.

## Registry update

Appended 14 corrected-Q sensitivity rows to `registry/case_registry.csv` from:

`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/corrected_case_manifest.csv`

The registry `source_id` is the corrected-Q `case_key`, and `source_owner` is `corrected_salt_q_sensitivity`. These rows are registered for provenance and table-building only; they are sensitivity/correlation-support perturbation rows, not nominal baseline rows.

## Reproduce

```bash
python3.11 tools/analyze/build_registry_corrected_q_status_table.py --strict-registry
python3.11 -m unittest tools.analyze.test_registry_corrected_q_status_table
```

The script reads case identities from `registry/case_registry.csv` and joins status evidence from:

- `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_gate_3280969_review/row_verdicts.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_corrected_salt_q_minimal_continuation_plan/convergence_resubmit_recommendations.csv`
