# AGENT-106 Journal

Date: `2026-06-23T09:45:00-05:00`
Role: `Coordinator / Implementer / Writer`
Task: `AGENT-106`

## Intent

Answer whether the live Water continuation pack and live `hiqbal3` pack are
near steady, then queue `normal`-partition follow-ons that do not collide with
the current live case directories.

## Observed state at start

- `3250776` `ethan_water_contpilot` was still running at about `21 h 52 m`.
- `3251883` `ethan_salt_hiqbal3` was still running at about `12 h 16 m`.
- The current packed launchers target the `256`-CPU `NuclearEnergy` nodes.
- Lonestar6 `normal` accepts the account, but not the literal partition name
  `general`.
- `normal` also carries the `qnormal` walltime cap of `2-00:00:00`.
- `normal` nodes expose `128` CPUs, while the dedicated `NuclearEnergy` nodes
  expose `256` CPUs.

## Action

- Verified from live case trees and `total_Q.dat` tails that:
  - Water is still mixed rather than uniformly flat
  - high-Q Salt is still useful but not yet a clean three-case steady endpoint
- Verified that a harmless `normal`-queue probe was accepted, then removed it.
- Submitted the Water follow-on as job `3253879`:
  - partition `normal`
  - dependency `afterany:3250776`
  - `2` nodes, `256` tasks, `48 h`
- Submitted the high-Q Salt follow-on as job `3253880`:
  - partition `normal`
  - dependency `afterany:3251883`
  - `2` nodes, `192` tasks, `48 h`
- Kept the existing defended `64`-rank-per-case layout unchanged.
- Recorded the new queue state and the `hiqbal3` follow-up note in both
  campaign dossiers.

## Completion

- The normal-queue handoff now exists and is safe against concurrent writes
  because both jobs wait on the live dedicated jobs to finish.
- The remaining decision is operational rather than technical: recheck whether
  `3253880` waits too long after its dependency clears.
