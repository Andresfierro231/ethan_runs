# Overnight Submit Decision Snapshot

Generated: `2026-07-07`

## Question

Decide whether a longer corrected Salt run should be submitted overnight.

## Inputs

- `live_salt_sanity_monitor.csv`
- `live_salt_sanity_monitor.json`
- `squeue -u $USER`
- `sacct -j 3275448,3275449,3275450,3275451,3275560,3279638,3279646 --format=JobID,JobName,Partition,State,Elapsed,Start,End,ExitCode -P`

## Scheduler Snapshot

| job | name | partition | state | dependency |
| --- | --- | --- | --- | --- |
| `3275448` | `corr_saltq_g1` | `NuclearEnergy` | `RUNNING` |  |
| `3275449` | `corr_saltq_g2` | `NuclearEnergy` | `RUNNING` |  |
| `3275560` | `corr_saltq_salt4_all` | `NuclearEnergy` | `RUNNING` |  |
| `3275450` | `corr_saltq_g3` | `NuclearEnergy` | `CANCELLED` |  |
| `3275451` | `corr_saltq_g4` | `NuclearEnergy` | `CANCELLED` |  |
| `3279638` | `saltq_gate_after` | `NuclearEnergy` | `CANCELLED` | superseded; old dependency was `afterany:3275448:3275449:3275560` |
| `3279646` | `saltq_gate_0707` | `NuclearEnergy` | `CANCELLED` | superseded; old dependency was `afterany:3275448:3275449:3275560` |

## Recommendation

Do not submit duplicate work for the currently running jobs tonight. Attempted
continuation submission for `corr_saltq_g1` after `3275448` was rejected by
Slurm because project `ASC23046` had `4633` SUs remaining and `4688` SUs already
requested by running/waiting jobs. The continuation plan remains technically
valid but is blocked by project balance until current/queued usage drops or an
alternate allocation is provided.

The premature gate jobs `3279638` and `3279646` were canceled so they cannot run
against partial live-job endpoints.

Prepare dependency-gated continuation submissions for the still-running groups
`3275448`, `3275449`, and `3275560` once Slurm balance allows it, because the
live cases have advanced only about `16-30%` of the target extension and still
have roughly `4.3-5.0 ks` of simulated time remaining.

Submit a targeted replacement only if the Salt 3 high-Q perturbations are needed:
`salt3_jin_hi5q_corrected` and `salt3_jin_hi10q_corrected` came from canceled
job `3275450`, have fatal/error markers, and advanced only about `20 s`.

Hold Salt 1 corrected perturbations for coordinator review. In particular,
`salt1_jin_hi10q_corrected` ended after only `254 s` past restart and carries
`needs_special_gate_scrutiny=True`; it is not closure-fit admissible.

## Files

- `overnight_submit_decision.csv`
- `overnight_submit_decision.json`
- `live_salt_sanity_monitor.csv`
- `live_salt_sanity_monitor.json`
- `README.md`
