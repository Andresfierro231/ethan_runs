# 2026-06-23 Ethan Runs

## Normal-Queue Follow-Ons

### Observed Output

- The live packed Water continuation job `3250776` had run about `21 h 52 m`
  at the check time.
- The live high-Q balanced Salt job `3251883` had run about `12 h 16 m` at the
  same check time.
- Lonestar6 does not expose a partition literally named `general`; the
  general-purpose CPU queue is `normal`.
- A harmless `normal` probe (`3253780`) was accepted and then canceled after
  confirmation.
- `normal` rejected the first Water and `hiqbal3` follow-on attempts because
  `qnormal` caps walltime at `2-00:00:00`.
- `normal` nodes expose `128` CPUs, while the dedicated `NuclearEnergy` nodes
  used by the live Ethan jobs expose `256` CPUs.

### Interpretation

- The Water and `hiqbal3` follow-ons are portable to the general-purpose queue,
  but not as literal one-node copies of the current dedicated-node packs.
- The right safe handoff is to preserve the defended `64`-rank-per-case
  packing while expanding the portable jobs to `2` normal nodes and capping the
  requested walltime at `48 h`.
- The follow-ons should wait on the current live jobs rather than touch the
  same case directories concurrently.

### Actions

- Submitted Water follow-on `3253879` `ethan_water_cont_nq`:
  - partition `normal`
  - dependency `afterany:3250776`
  - `2` nodes
  - `256` tasks
  - `48 h`
- Submitted high-Q Salt follow-on `3253880` `ethan_salt_hiqb3_nq`:
  - partition `normal`
  - dependency `afterany:3251883`
  - `2` nodes
  - `192` tasks
  - `48 h`
- Per the later queue-cutover request, canceled the live dedicated jobs:
  - `3250776` `ethan_water_contpilot` at `2026-06-23 09:58 CDT`
  - `3251883` `ethan_salt_hiqbal3` at `2026-06-23 09:58 CDT`
- That immediately released the queued `normal` follow-ons from dependency hold
  to ordinary `Priority` pending state.

### Current steady-state boundary

- Water is still mixed rather than uniformly steady:
  - Water 1 last-`4 s` `total_Q` drift: `+0.0067 W`
  - Water 2 last-`4 s` `total_Q` drift: `-0.0102 W`
  - Water 3 last-`4 s` `total_Q` drift: `-0.0107 W`
  - Water 4 last-`4 s` `total_Q` drift: `-0.0355 W`
- The high-Q balanced Salt pack is also not yet uniformly steady:
  - Salt 2 high-Q last-`4 s` `total_Q` drift: `-0.0009 W`
  - Salt 3 high-Q last-`4 s` `total_Q` drift: `+0.0415 W`
  - Salt 4 high-Q last-`4 s` `total_Q` drift: `+0.0643 W`

### Next suggested action

- Recheck `3253880` after dependency release. If the `normal` queue wait is too
  long, queue a different `hiqbal3` follow-on behind the live high-Q lane
  rather than letting that path go cold.

## CFD Temporary Checkpoint

### Observed Output

- A temporary checkpoint audit was taken on `2026-06-23` so the current late
  windows could be analyzed as if they were a bounded dataset.
- During that checkpoint pass, four CFD submissions were canceled by mistake:
  - `3250777` `ethan_salt_contpack` at `10:25 CDT`
  - `3251884` `ethan_salt_loqbal3` at `10:25 CDT`
  - `3253879` `ethan_water_cont_nq` before start
  - `3253880` `ethan_salt_hiqb3_nq` before start
- The user then clarified that "freeze" meant "copy the latest retained window
  into a temporary analysis folder," not "stop the background runs."
- Recovery submissions were immediately requeued at `2026-06-23 10:34:58 CDT`:
  - `3254178` `ethan_salt_contpack` on `NuclearEnergy`
  - `3254179` `ethan_salt_loqbal3` on `NuclearEnergy`
  - `3254180` `ethan_water_cont_nq` on `normal`
  - `3254181` `ethan_salt_hiqb3_nq` on `normal`
- Salt 2-4 all preserved at least `20` representative retained saved times in
  the checkpointed continuation and scenario lanes.
- Salt 1 did not: the checkpointed Salt 1 reference lane preserved only `18`
  saved times.

### Interpretation

- The checkpoint package is valid as a bounded analysis snapshot, but it is not
  the final CFD endpoint because the continuations were requeued immediately
  after the user clarified the intent.
- Salt 2-4 satisfy the requested minimum retained-window inventory for the
  snapshot package.
- Salt 1 can still be used as a reference lane, but not as a fully comparable
  `20`-step retained representative lane.
- The Water `4 x 64` pilot looked operationally acceptable on a dedicated
  `256`-CPU node: all four lanes advanced, all four preserved a full `20`-step
  representative window, and no OOM or node-failure signature appeared before
  the mistaken cancellation.
- That operational health did not imply convergence. Water 4 remained the least
  settled of the four Water lanes.

### Actions

- Requeued the canceled continuation jobs so CFD collection continues in the
  background:
  - `3254178` `ethan_salt_contpack`
  - `3254179` `ethan_salt_loqbal3`
  - `3254180` `ethan_water_cont_nq`
  - `3254181` `ethan_salt_hiqb3_nq`
- Verified the immediate queue state after resubmission:
  - `3254178` pending on `Resources`
  - `3254179` pending on `Priority`
  - `3254180` pending on `Priority`
  - `3254181` pending on `Priority`

### Artifacts

- Checkpoint package: `reports/2026-06-23_ethan_cfd_freeze_checkpoint/`
- Temporary Salt checkpoint copy root:
  `tmp/2026-06-23_salt_last20_checkpoint/`
  - the background copy was still materializing at the journal update time
