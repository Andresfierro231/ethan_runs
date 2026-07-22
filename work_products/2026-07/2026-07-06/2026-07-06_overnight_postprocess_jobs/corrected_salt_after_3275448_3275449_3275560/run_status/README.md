# Post-Processing Run Status Inventory

Generated: `2026-07-09T12:23:43-05:00`

## Job Summary

| job | state | cases | job recommendation |
| --- | --- | ---: | --- |
| `3275560` `corrected_saltq_all_prepared` | `AFTERANY_COMPLETE` | 14 | `no_more_runtime_needed_document_only` |

## Recommendation Counts

- `document_only_false_steady`: `14`

## Notes

- Salt Q perturbations are closure-fit admissible only when the operating-point gate returns `requalified`.
- Running Water cases should be frozen and reprocessed after the Slurm job exits.
- This inventory is monitor-based; field reconstruction/extraction remains a separate Slurm/dev-node workflow.
