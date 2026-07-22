# Live Corrected Salt Sanity Monitor

Generated: `2026-07-07`

## Scope

Read-only inspection of corrected Salt Q solver logs, launch preflight audits, mdot monitors, and Slurm state.

## Slurm

- Formal gate job: `3293924`
- Dependency: `afterany:3293924`
- Gate state: `TIMEOUT`
- Gate partition: `NuclearEnergy`

## Summary

- Cases scanned: `14`
- Cases with `needs_special_gate_scrutiny=True`: `14`
- Fatal/error-marker cases: `14`

## Case Snapshot

| case | job | partition | state | latest time s | fatal/error markers | recommendation |
| --- | --- | --- | --- | ---: | ---: | --- |
| `salt1_jin_lo10q_corrected` | `` | `` | `` | 8016.75 | 3 | `investigate` |
| `salt1_jin_hi10q_corrected` | `` | `` | `` | 5587.99 | 2 | `investigate` |
| `salt2_jin_lo10q_corrected` | `` | `` | `` | 12382.8 | 3 | `investigate` |
| `salt2_jin_lo5q_corrected` | `` | `` | `` | 10275.9 | 3 | `investigate` |
| `salt2_jin_hi5q_corrected` | `` | `` | `` | 9780.59 | 4 | `investigate` |
| `salt2_jin_hi10q_corrected` | `` | `` | `` | 11668.6 | 3 | `investigate` |
| `salt3_jin_lo10q_corrected` | `` | `` | `` | 9428.16 | 3 | `investigate` |
| `salt3_jin_lo5q_corrected` | `` | `` | `` | 9389.17 | 2 | `investigate` |
| `salt3_jin_hi5q_corrected` | `` | `` | `` | 7639.48 | 3 | `investigate` |
| `salt3_jin_hi10q_corrected` | `` | `` | `` | 7637.88 | 4 | `investigate` |
| `salt4_jin_lo10q_corrected` | `` | `` | `` | 13421.5 | 2 | `investigate` |
| `salt4_jin_lo5q_corrected` | `` | `` | `` | 11695.2 | 3 | `investigate` |
| `salt4_jin_hi5q_corrected` | `` | `` | `` | 11399.2 | 3 | `investigate` |
| `salt4_jin_hi10q_corrected` | `` | `` | `` | 14017.4 | 5 | `investigate` |

## Admission Rule

This monitor does not admit closure-fit rows. It can only recommend hold/investigate/admit-candidate-pending-formal-gate. Any row with `needs_special_gate_scrutiny=True` is not closure-fit admissible without coordinator review, even if later postprocessing reports `operating_point_verdict=requalified`.

## Flagged Rows

| case | recommendation | reason |
| --- | --- | --- |
| `salt1_jin_lo10q_corrected` | `investigate` | fatal/error markers=3; missing nominal mdot reference |
| `salt1_jin_hi10q_corrected` | `investigate` | fatal/error markers=2; missing nominal mdot reference |
| `salt2_jin_lo10q_corrected` | `investigate` | fatal/error markers=3 |
| `salt2_jin_lo5q_corrected` | `investigate` | fatal/error markers=3 |
| `salt2_jin_hi5q_corrected` | `investigate` | fatal/error markers=4 |
| `salt2_jin_hi10q_corrected` | `investigate` | fatal/error markers=3 |
| `salt3_jin_lo10q_corrected` | `investigate` | fatal/error markers=3 |
| `salt3_jin_lo5q_corrected` | `investigate` | fatal/error markers=2 |
| `salt3_jin_hi5q_corrected` | `investigate` | fatal/error markers=3 |
| `salt3_jin_hi10q_corrected` | `investigate` | fatal/error markers=4 |
| `salt4_jin_lo10q_corrected` | `investigate` | fatal/error markers=2 |
| `salt4_jin_lo5q_corrected` | `investigate` | fatal/error markers=3 |
| `salt4_jin_hi5q_corrected` | `investigate` | fatal/error markers=3 |
| `salt4_jin_hi10q_corrected` | `investigate` | fatal/error markers=5 |

## Files

- `live_salt_sanity_monitor.csv`
- `live_salt_sanity_monitor.json`
