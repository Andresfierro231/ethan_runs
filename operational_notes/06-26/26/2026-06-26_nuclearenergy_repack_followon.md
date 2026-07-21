# 2026-06-26 NuclearEnergy Repack Follow-On

## Purpose

Repack the pending June 25 `normal`-queue continuation and Salt boundary set
into four `NuclearEnergy` submissions after the user received permission for
two additional `NuclearEnergy` nodes.

## Requested mapping

- immediate `6 d` packed job on `2` `NuclearEnergy` nodes:
  - `salt1_jin_basecont`
  - `salt1_jin_hiq_balq`
  - `salt2_jin_hiq_balq`
  - `salt3_jin_hiq_balq`
- immediate `6 d` packed job on `2` `NuclearEnergy` nodes:
  - `salt4_jin_hiq_balq`
  - `salt1_jin_loq_balq`
  - `salt2_jin_hi5q_balq`
  - `salt2_jin_lo5q_balq`
- queued `afterany` behind one currently running `NuclearEnergy` job:
  - `salt3_jin_hi5q_balq`
  - `salt3_jin_lo5q_balq`
  - `salt4_jin_hi5q_balq`
  - `salt4_jin_lo5q_balq`
- queued `afterany` behind the other currently running `NuclearEnergy` job:
  - `water1`
  - `water2`
  - `water3`
  - `water4`

## Partition limit adjustment

The requested `6 d` walltime cannot be submitted on `NuclearEnergy`. The
partition currently reports a hard maximum of `5-00:00:00`, so the repacked
submissions use `120 h` while preserving the requested case grouping and
dependency structure.

## Superseded queue state

The pending `normal` jobs `3259055-3259094` represented eight five-segment
`48 h` chains. They are superseded by this repack and should be canceled before
the new jobs are submitted so the same cases do not later run concurrently on
two different campaign paths.

## Existing running dependency anchors

- `3254178` `ethan_salt_contpack`
- `3254179` `ethan_salt_loqbal3`

The remaining Salt midpoint pack should queue behind one of those jobs, and the
Water continuation pack should queue behind the other.

## Implemented submission

- canceled superseded `normal` jobs:
  - `3259055-3259094`
- submitted immediate `NuclearEnergy` jobs at `120 h`:
  - `3261320` `ethan_s123hi_ne5d`
    - `salt1_jin_basecont`
    - `salt1_jin_hiq_balq`
    - `salt2_jin_hiq_balq`
    - `salt3_jin_hiq_balq`
  - `3261321` `ethan_s41lo2mid_ne5d`
    - `salt4_jin_hiq_balq`
    - `salt1_jin_loq_balq`
    - `salt2_jin_hi5q_balq`
    - `salt2_jin_lo5q_balq`
- submitted dependent `NuclearEnergy` jobs at `120 h`:
  - `3261322` `ethan_s34mid_ne5d`
    - dependency: `afterany:3254179`
    - `salt3_jin_hi5q_balq`
    - `salt3_jin_lo5q_balq`
    - `salt4_jin_hi5q_balq`
    - `salt4_jin_lo5q_balq`
  - `3261323` `ethan_w1234_ne5d`
    - dependency: `afterany:3254178`
    - `water1`
    - `water2`
    - `water3`
    - `water4`

## Queue snapshot after submission

- `3261320` `RUNNING` on `c318-[012-013]`
- `3261321` `RUNNING` on `c318-[014-015]`
- `3261322` `PENDING` with reason `Dependency`
- `3261323` `PENDING` with reason `Dependency`
- anchor jobs still running:
  - `3254178` `RUNNING` on `c318-011`
  - `3254179` `RUNNING` on `c318-016`

## 2026-06-29 Correction

- The user clarified that these four-case `NuclearEnergy` packs should have
  been submitted on `1` node, not `2`.
- Live inspection on `2026-06-29` showed jobs `3261320-3261323` each hold a
  `2`-node allocation even though the launcher only starts four `64`-task
  `foamRun` steps.
- Step placement was also not cleanly balanced across the two nodes. At least
  two live jobs had a `3 + 1` split across their allocated nodes, and two
  jobs had all still-running steps visible on a single node after earlier
  steps completed.
- The launcher `tmp/2026-06-26_nuclearenergy_repack_followon/run_packed_four_case_nuclear.sbatch`
  has been corrected to request `#SBATCH -N 1` while keeping `#SBATCH -n 256`.
- Operational rule going forward: for `NuclearEnergy`, default to `1` node and
  only request more than `1` node when there is an explicit case-specific
  justification.
- On `2026-06-29`, the original mispacked jobs were canceled and replaced by
  immediate single-node submissions:
  - `3265972` `ethan_s123hi_ne5d` replaces `3261320`
  - `3265971` `ethan_s41lo2mid_ne5d` replaces `3261321`
  - `3265969` `ethan_s34mid_ne5d` replaces `3261322`
  - `3265970` `ethan_w1234_ne5d` replaces `3261323`
- Live verification after resubmission showed each corrected job running with
  `NumNodes=1`, `NumCPUs=256`, and a single-node `NodeList`.
