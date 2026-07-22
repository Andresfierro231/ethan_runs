# Post-Processing Run Status Inventory

Generated: `2026-07-04T08:49:47-05:00`

## Job Summary

| job | state | cases | job recommendation |
| --- | --- | ---: | --- |
| `3265969` `ethan_s34mid_ne5d` | `CANCELLED` | 4 | `no_more_runtime_needed_document_only` |
| `3265970` `ethan_w1234_ne5d` | `RUNNING` | 4 | `let_water_finish_then_freeze` |
| `3265971` `ethan_s41lo2mid_ne5d` | `CANCELLED` | 4 | `no_more_runtime_needed_document_only` |
| `3265972` `ethan_s123hi_ne5d` | `CANCELLED` | 4 | `postprocess_nominal_only_document_false_steady` |

## Recommendation Counts

- `document_only_false_steady`: `11`
- `postprocess_if_needed`: `1`
- `wait_for_job_exit_then_freeze`: `4`

## Notes

- Salt Q perturbations are closure-fit admissible only when the operating-point gate returns `requalified`.
- Running Water cases should be frozen and reprocessed after the Slurm job exits.
- This inventory is monitor-based; field reconstruction/extraction remains a separate Slurm/dev-node workflow.
