# Live Corrected Salt Sanity Monitor

Generated: `2026-07-07`

## Scope

Read-only inspection of corrected Salt Q solver logs, launch preflight audits, mdot monitors, and Slurm state.

## Slurm

- Formal gate job: `3279646`
- Dependency: `afterany:3275448:3275449:3275560`
- Gate state: `PENDING`
- Gate partition: `NuclearEnergy`

## Summary

- Cases scanned: `14`
- Cases with `needs_special_gate_scrutiny=True`: `4`
- Fatal/error-marker cases: `2`

## Case Snapshot

| case | job | partition | state | latest time s | fatal/error markers | recommendation |
| --- | --- | --- | --- | ---: | ---: | --- |
| `salt1_jin_lo10q_corrected` | `3275448` | `NuclearEnergy` | `RUNNING` | 5440.12 | 0 | `hold_for_coordinator_review` |
| `salt1_jin_hi10q_corrected` | `3275448` | `NuclearEnergy` | `RUNNING` | 4010.59 | 0 | `hold_for_coordinator_review` |
| `salt2_jin_lo10q_corrected` | `3275448` | `NuclearEnergy` | `RUNNING` | 9430.9 | 0 | `hold_running_wait_for_formal_gate` |
| `salt2_jin_lo5q_corrected` | `3275448` | `NuclearEnergy` | `RUNNING` | 9432.94 | 0 | `hold_running_wait_for_formal_gate` |
| `salt2_jin_hi5q_corrected` | `3275449` | `NuclearEnergy` | `RUNNING` | 9110.31 | 0 | `hold_running_wait_for_formal_gate` |
| `salt2_jin_hi10q_corrected` | `3275449` | `NuclearEnergy` | `RUNNING` | 9039.81 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_lo10q_corrected` | `3275449` | `NuclearEnergy` | `RUNNING` | 8777.99 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_lo5q_corrected` | `3275449` | `NuclearEnergy` | `RUNNING` | 8757.24 | 0 | `hold_running_wait_for_formal_gate` |
| `salt3_jin_hi5q_corrected` | `3275450` | `NuclearEnergy` | `CANCELLED by 890970` | 7639.48 | 3 | `investigate` |
| `salt3_jin_hi10q_corrected` | `3275450` | `NuclearEnergy` | `CANCELLED by 890970` | 7637.88 | 4 | `investigate` |
| `salt4_jin_lo10q_corrected` | `3275560` | `NuclearEnergy` | `RUNNING` | 11044.9 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_lo5q_corrected` | `3275560` | `NuclearEnergy` | `RUNNING` | 11079.9 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_hi5q_corrected` | `3275560` | `NuclearEnergy` | `RUNNING` | 10879.1 | 0 | `hold_running_wait_for_formal_gate` |
| `salt4_jin_hi10q_corrected` | `3275560` | `NuclearEnergy` | `RUNNING` | 10967.6 | 0 | `hold_running_wait_for_formal_gate` |

## Admission Rule

This monitor does not admit closure-fit rows. It can only recommend hold/investigate/admit-candidate-pending-formal-gate. Any row with `needs_special_gate_scrutiny=True` is not closure-fit admissible without coordinator review, even if later postprocessing reports `operating_point_verdict=requalified`.

## Flagged Rows

| case | recommendation | reason |
| --- | --- | --- |
| `salt1_jin_lo10q_corrected` | `hold_for_coordinator_review` | missing nominal mdot reference |
| `salt1_jin_hi10q_corrected` | `hold_for_coordinator_review` | missing nominal mdot reference; ended early after 254s past restart (4.24% of target extension) |
| `salt3_jin_hi5q_corrected` | `investigate` | fatal/error markers=3; terminal/non-success scheduler state=CANCELLED by 890970; terminal short advance after 21.5s past restart (0.36% of target extension) |
| `salt3_jin_hi10q_corrected` | `investigate` | fatal/error markers=4; terminal/non-success scheduler state=CANCELLED by 890970; terminal short advance after 19.9s past restart (0.33% of target extension) |

## Files

- `live_salt_sanity_monitor.csv`
- `live_salt_sanity_monitor.json`
