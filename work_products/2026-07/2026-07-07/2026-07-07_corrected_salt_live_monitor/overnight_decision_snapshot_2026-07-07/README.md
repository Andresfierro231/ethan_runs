# Live Corrected Salt Sanity Monitor

Generated: `2026-07-07`

## Scope

Read-only inspection of corrected Salt Q solver logs, launch preflight audits, mdot monitors, and Slurm state.

## Slurm

- Formal gate job: `3279646`
- Dependency: `afterany:3275448:3275449:3275560`
- Gate state: `unknown`
- Gate partition: ``

## Summary

- Cases scanned: `14`
- Cases with `needs_special_gate_scrutiny=True`: `4`
- Fatal/error-marker cases: `2`

## Case Snapshot

| case | job | partition | state | latest time s | fatal/error markers | recommendation |
| --- | --- | --- | --- | ---: | ---: | --- |
| `salt1_jin_lo10q_corrected` | `3275448` | `` | `` | 5585.28 | 0 | `hold_for_coordinator_review` |
| `salt1_jin_hi10q_corrected` | `3275448` | `` | `` | 4010.59 | 0 | `hold_for_coordinator_review` |
| `salt2_jin_lo10q_corrected` | `3275448` | `` | `` | 9563 | 0 | `hold_running_wait_for_formal_gate` |
| `salt2_jin_lo5q_corrected` | `3275448` | `` | `` | 9563.54 | 0 | `hold_running_wait_for_formal_gate` |
| `salt2_jin_hi5q_corrected` | `3275449` | `` | `` | 9216.24 | 0 | `hold_running_wait_for_formal_gate` |
| `salt2_jin_hi10q_corrected` | `3275449` | `` | `` | 9137.54 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_lo10q_corrected` | `3275449` | `` | `` | 8879.84 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_lo5q_corrected` | `3275449` | `` | `` | 8855.27 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_hi5q_corrected` | `3275450` | `` | `` | 7639.48 | 3 | `investigate` |
| `salt3_jin_hi10q_corrected` | `3275450` | `` | `` | 7637.88 | 4 | `investigate` |
| `salt4_jin_lo10q_corrected` | `3275560` | `` | `` | 11136.7 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_lo5q_corrected` | `3275560` | `` | `` | 11172.4 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_hi5q_corrected` | `3275560` | `` | `` | 10956.6 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_hi10q_corrected` | `3275560` | `` | `` | 11053.3 | 0 | `hold_running_wait_for_formal_gate` |

## Admission Rule

This monitor does not admit closure-fit rows. It can only recommend hold/investigate/admit-candidate-pending-formal-gate. Any row with `needs_special_gate_scrutiny=True` is not closure-fit admissible without coordinator review, even if later postprocessing reports `operating_point_verdict=requalified`.

## Flagged Rows

| case | recommendation | reason |
| --- | --- | --- |
| `salt1_jin_lo10q_corrected` | `hold_for_coordinator_review` | missing nominal mdot reference |
| `salt1_jin_hi10q_corrected` | `hold_for_coordinator_review` | missing nominal mdot reference; ended early after 254s past restart (4.24% of target extension) |
| `salt3_jin_hi5q_corrected` | `investigate` | fatal/error markers=3 |
| `salt3_jin_hi10q_corrected` | `investigate` | fatal/error markers=4 |

## Files

- `live_salt_sanity_monitor.csv`
- `live_salt_sanity_monitor.json`
