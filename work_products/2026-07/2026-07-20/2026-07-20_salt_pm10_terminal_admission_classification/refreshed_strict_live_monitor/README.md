# Live Corrected Salt Sanity Monitor

Generated: `2026-07-20T15:56:07.379076+00:00`

## Scope

Read-only inspection of corrected Salt Q solver logs, launch preflight audits, mdot monitors, and Slurm state.

## Slurm

- Formal gate job: `3279646`
- Dependency: `afterany:3275448:3275449:3275560`
- Gate state: `unknown`
- Gate partition: ``

## Summary

- Cases scanned: `14`
- Cases with `needs_special_gate_scrutiny=True`: `2`
- Fatal/error-marker cases: `0`

## Case Snapshot

| case | job | partition | state | latest time s | fatal/error markers | recommendation |
| --- | --- | --- | --- | ---: | ---: | --- |
| `salt1_jin_lo10q_corrected` | `3275448` | `` | `` | 8016.75 | 0 | `hold_for_coordinator_review` |
| `salt1_jin_hi10q_corrected` | `3275448` | `` | `` | 5587.99 | 0 | `hold_for_coordinator_review` |
| `salt2_jin_lo10q_corrected` | `3275448` | `` | `` | 12382.8 | 0 | `hold_running_wait_for_formal_gate` |
| `salt2_jin_lo5q_corrected` | `3275448` | `` | `` | 10275.9 | 0 | `hold_running_wait_for_formal_gate` |
| `salt2_jin_hi5q_corrected` | `3275449` | `` | `` | 9780.59 | 0 | `hold_running_wait_for_formal_gate` |
| `salt2_jin_hi10q_corrected` | `3275449` | `` | `` | 11668.6 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_lo10q_corrected` | `3275449` | `` | `` | 9428.16 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_lo5q_corrected` | `3275449` | `` | `` | 9389.17 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_hi5q_corrected` | `3275450` | `` | `` | 7639.48 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_hi10q_corrected` | `3275450` | `` | `` | 7637.88 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_lo10q_corrected` | `3275560` | `` | `` | 13421.5 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_lo5q_corrected` | `3275560` | `` | `` | 11695.2 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_hi5q_corrected` | `3275560` | `` | `` | 11399.2 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_hi10q_corrected` | `3275560` | `` | `` | 14017.4 | 0 | `hold_running_wait_for_formal_gate` |

## Admission Rule

This monitor does not admit closure-fit rows. It can only recommend hold/investigate/admit-candidate-pending-formal-gate. Any row with `needs_special_gate_scrutiny=True` is not closure-fit admissible without coordinator review, even if later postprocessing reports `operating_point_verdict=requalified`.

## Flagged Rows

| case | recommendation | reason |
| --- | --- | --- |
| `salt1_jin_lo10q_corrected` | `hold_for_coordinator_review` | missing nominal mdot reference |
| `salt1_jin_hi10q_corrected` | `hold_for_coordinator_review` | missing nominal mdot reference |

## Files

- `live_salt_sanity_monitor.csv`
- `live_salt_sanity_monitor.json`
