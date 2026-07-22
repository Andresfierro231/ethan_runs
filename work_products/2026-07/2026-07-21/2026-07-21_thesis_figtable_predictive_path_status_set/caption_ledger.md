# Predictive Path Caption Ledger

| Artifact | Caption rule |
| --- | --- |
| `runtime_input_contract_table.csv` | Setup-known fields are runtime inputs; CFD responses and validation temperatures are not. |
| `split_separation_table.csv` | Train/support, validation, holdout, and external-test roles are separated before scoring. |
| `blocked_gate_status_table.csv` | Pressure, thermal, and recirculation lanes remain blocked or diagnostic until named gates pass. |
| `negative_results_evidence_table.csv` | Negative S8/S9/S10/S12 results are scientific evidence, not closure admissions. |
| `predictive_path_status_diagram.md` | The path is sequential; no protected-row scoring occurs before freeze. |
