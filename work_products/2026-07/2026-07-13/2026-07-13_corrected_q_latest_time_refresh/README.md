# Corrected-Q Latest-Time Refresh

Task: `AGENT-261`

This package reruns the registry-driven corrected-Q status table builder into a
July 13 output directory and compares the selected live rows against the July 10
latest-time package.

## Result

- `python3.11 -m unittest tools.analyze.test_registry_corrected_q_status_table`
  passed.
- `python3.11 tools/analyze/build_registry_corrected_q_status_table.py --strict-registry --output-dir work_products/2026-07/2026-07-13/2026-07-13_corrected_q_latest_time_refresh`
  passed.
- Strict registry coverage remains clean for all 14 corrected-Q manifest rows.
- No admission state changed.

## Latest-Time Delta

| row | July 10 written | July 13 written | written delta | July 10 log | July 13 log | log delta | interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Salt1 -10Q | 6544.000 s | 8013.000 s | 1469.000 s | 6544.688 s | 8013.299 s | 1468.611 s | Meaningful written and log advance. |
| Salt1 +10Q | 4166.000 s | 5548.000 s | 1382.000 s | 4166.873 s | 5548.994 s | 1382.121 s | Meaningful written and log advance. |
| Salt4 +10Q | 11537.000 s | 12607.000 s | 1070.000 s | 11537.723 s | 11540.098 s | 2.375 s | Meaningful written advance only; parsed log tail did not advance meaningfully. |

## Boundary

These remain corrected-Q sensitivity/correlation-support rows. This refresh is
not a post-exit gate, does not admit any row into closure fitting, and does not
change the registry or native solver outputs.

## Outputs

- `selected_corrected_q_status_table.csv` / `.md`
- `all_corrected_q_status_table.csv` / `.md`
- `corrected_q_latest_timesteps.csv`
- `corrected_q_registry_coverage.csv`
- `latest_time_delta_vs_2026-07-10.csv`
- `summary.json`
