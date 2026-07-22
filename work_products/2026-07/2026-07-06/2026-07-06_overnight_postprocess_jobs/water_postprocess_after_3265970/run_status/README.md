# Post-Processing Run Status Inventory

Generated: `2026-07-06T19:26:37-05:00`

## Job Summary

| job | state | cases | job recommendation |
| --- | --- | ---: | --- |
| `3265969` `ethan_s34mid_ne5d` | `CANCELLED` | 4 | `no_more_runtime_needed_document_only` |
| `3265970` `ethan_w1234_ne5d` | `TIMEOUT` | 4 | `freeze_and_postprocess_water` |
| `3265971` `ethan_s41lo2mid_ne5d` | `CANCELLED` | 4 | `no_more_runtime_needed_document_only` |
| `3265972` `ethan_s123hi_ne5d` | `CANCELLED` | 4 | `postprocess_nominal_only_document_false_steady` |

## Recommendation Counts

- `document_only_false_steady`: `11`
- `freeze_and_postprocess_water`: `4`
- `postprocess_if_needed`: `1`

## Notes

- Salt Q perturbations are closure-fit admissible only when the operating-point gate returns `requalified`.
- Running Water cases should be frozen and reprocessed after the Slurm job exits.
- This inventory is monitor-based; field reconstruction/extraction remains a separate Slurm/dev-node workflow.
