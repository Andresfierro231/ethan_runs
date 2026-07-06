# 2026-06-19 Ethan Blocker And 1D Follow-On Wave

## Purpose

This campaign submits the first bounded Salt-only scenario-expansion wave after
the June 19 closure-to-modeling v3 handoff.

The wave stays deliberately narrow:

- it does not reopen shared extractor files;
- it does not assume a readable cooler-`h` mutation path that the workspace
  cannot actually prove;
- it now prioritizes visible heater and cooling-branch residual controls ahead
  of insulation-only variation;
- it brackets the current defended Salt domain with Salt 2 Jin and Salt 4 Jin;
- it now includes the Salt 3 Jin midpoint pair because the June 22 user
  request explicitly widened the bracket scope.

## Why these runs

- Ongoing Salt/Water continuations remain the main blocker-first CFD path for
  retained-time closure support.
- The next justified new scenarios are Salt-only, because Water still remains
  readiness-only.
- Salt 2 Jin and Salt 4 Jin were chosen because they bracket the currently
  defended Salt fit domain better than Salt 1, while staying smaller than a
  full 8-child envelope submission.

## Current campaign state on 2026-06-22

### Rebalanced bracket-wave queue on 2026-06-22

- `salt2_jin_hiq_hiins`
  - canceled unbalanced relaunch job: `3250783`
  - balanced packed replacement job: `3251883`
  - current state: pending in packed high-Q node
- `salt2_jin_loq_loins`
  - canceled unbalanced relaunch job: `3250779`
  - balanced packed replacement job: `3251884`
  - current state: pending in packed low-Q node
- `salt3_jin_hiq_hiins`
  - canceled unbalanced release job: `3250782`
  - balanced packed replacement job: `3251883`
  - current state: pending in packed high-Q node
- `salt3_jin_loq_loins`
  - canceled unbalanced release job: `3250781`
  - balanced packed replacement job: `3251884`
  - current state: pending in packed low-Q node
- `salt4_jin_hiq_hiins`
  - canceled unbalanced repaired relaunch job: `3250778`
  - balanced packed replacement job: `3251883`
  - current state: pending in packed high-Q node
- `salt4_jin_loq_loins`
  - canceled unbalanced repaired relaunch job: `3250780`
  - balanced packed replacement job: `3251884`
  - current state: pending in packed low-Q node

### June 22 retention, packing, and heat-contract correction

- all six bracket cases still preserve `purgeWrite 21`
- the earlier June 19 / June 22 bracket job IDs were canceled during the
  capped-window stop because `purgeWrite 5` retained only about `4 s` of
  restart history
- the later June 22 unbalanced relaunches (`3250778`-`3250783`) were canceled
  again after the heat-balance gate tightened to `|Q_in - Q_lost| < 2 W`
- the current queue target is therefore two packed `3 x 64` balanced nodes:
  - `3251883` `ethan_salt_hiqbal3`
  - `3251884` `ethan_salt_loqbal3`

### Diagnosed June 19 failures and repairs

- original Salt 4 jobs failed immediately:
  - `3246562` `ethan_s4j_hiqins`
  - `3246563` `ethan_s4j_loqins`
- failure mode:
  - staged trees were missing `system/controlDict`
- preserved evidence:
  - `failed_stage_preserved/2026-06-22_salt4_bracket_repair/`
- repair actions:
  - rebuilt the Salt 4 children from the static continuation parent
  - re-applied only the intended mutated `0/T` and `case_config.yaml`
  - hardened `scripts/run_continuation_generic_openfoam13.sbatch` so missing
    `0/`, `constant/`, `system/`, or `system/controlDict` is rejected before
    the solver start

## Boundary-behavior goals for the next follow-on

The June 22 user retargeting makes the purpose of the Salt bracket wave more
explicit than a simple insulation sweep:

- maximize the heater-to-cooler temperature difference where the current setup
  allows it
- minimize the heater-to-cooler temperature difference
- locate the transition region that starts to favor upcomer recirculation
- test what changes development length the most
- keep heater/cooler operating-point effects ahead of insulation-only tuning in
  the next DOE expansion

Current blocker:

- the readable cooler branch in the staged cases still presents as fixed-`Q`, so
  this wave still cannot prove a clean cooler-`h` mutation path

## Mutation rules after the June 22 heat-gate repair

- `hiQ_balQ_baselineIns`:
  - lower-heater patch `Q` scaled by `+10%`
  - baseline insulation restored
  - cooling-branch fixed sinks re-solved from the parent late-window ledger
- `loQ_balQ_baselineIns`:
  - lower-heater patch `Q` scaled by `-10%`
  - baseline insulation restored
  - cooling-branch fixed sinks re-solved from the parent late-window ledger

The powered test-section patch remains fixed.

The readable cooler branch remains fixed-`Q`, so no cooler-`h` mutation is
applied in this wave. The June 22 repair therefore uses only heater and
cooling-branch residual changes.

## Heat-balance repair outcome

The original six bracket relaunches were not strict balance-by-construction
heater/cooler DOE children.

What changed in the canceled relaunches:

- lower-heater `Q` was moved up or down by `10%`
- insulation thickness moved by `±0.40 in`

What did not change:

- the three cooling-branch fixed `Q` sink patches in `0/T`

So the canceled relaunches missed the new reference-state
`Q_in - Q_lost ≈ 0` staging contract with `Q_lost = Q_removed + Q_ambient` by
large margins even before counting the additional ambient-loss drift caused by
the `±0.40 in` insulation change:

- Salt 2 high-Q: lower-bound residual `+26.93 W`
- Salt 2 low-Q: lower-bound residual `-26.21 W`
- Salt 3 high-Q: lower-bound residual `+30.72 W`
- Salt 3 low-Q: lower-bound residual `-28.78 W`
- Salt 4 high-Q: lower-bound residual `+34.13 W`
- Salt 4 low-Q: lower-bound residual `-33.39 W`

The June 22 packed replacements fix that by:

- restoring baseline insulation in all six staged roots
- keeping the `+/-10%` heater mutation
- solving the cooling-branch fixed sink as the exact parent-ledger residual
- repacking the six cases as two `3 x 64` Salt nodes instead of six
  standalone 64-rank jobs

Future fixed-`Q` Salt DOE children should instead:

- derive the child cooling-branch sink from a parent late-window signed
  sectionwise heat ledger
- keep that arithmetic in the submission note or campaign manifest
- avoid using metadata `cooler_h_W_m2K` as if it were the authoritative live
  cooler control

## Reproduction

- campaign manifest: `campaign_manifest.csv`
- generic sbatch wrapper: `scripts/run_continuation_generic_openfoam13.sbatch`
- packed three-case launcher:
  `scripts/run_packed_three_case_openfoam13.sbatch`
- abandoned but reproducible fresh-copy staging helper:
  `scripts/stage_balanced_salt_bracket_cases.py`

## June 23 hiqbal3 normal-queue follow-on

- current high-Q balanced node:
  - job `3251883` `ethan_salt_hiqbal3`
  - wall-clock runtime at cutover: about `12 h 33 m`
  - canceled on `2026-06-23 09:58 CDT` so the queued normal follow-on could
    become eligible
- queued `normal` follow-on:
  - job `3253880` `ethan_salt_hiqb3_nq`
  - queue state after cutover: pending on `Priority`
  - requested layout: `2` normal nodes, `192` total tasks, `48 h`
- why the follow-on uses `2` normal nodes instead of `1`:
  - `normal` nodes expose `128` CPUs each
  - the defended balanced high-Q layout remains `3 x 64`
  - preserving that packing needs `192` CPUs, so the portable `normal`
    follow-on must span `2` nodes

## June 23 live-state check

The high-Q balanced Salt family is not yet uniformly steady:

- Salt 2 high-Q looks closest to flat (`-0.0009 W` over the last `4 s`)
- Salt 3 high-Q still drifts upward materially (`+0.0415 W` over the last `4 s`)
- Salt 4 high-Q still drifts upward materially (`+0.0643 W` over the last `4 s`)

So `hiqbal3` is still gathering useful continuation data, but the current live
high-Q node is not yet a clean three-case steady-state endpoint.

## June 23 temporary checkpoint and recovery

- a bounded checkpoint snapshot was recorded on `2026-06-23` so the current
  retained high-Q and low-Q windows could be analyzed without waiting for final
  convergence
- during that pass, the live low-Q balanced node `3251884` and the queued
  normal high-Q follow-on `3253880` were canceled by mistake
- the user clarified that "freeze" meant "copy the latest retained window into
  a temporary analysis folder," not "stop the background jobs"
- the wave was therefore recovered immediately with:
  - `3254179` `ethan_salt_loqbal3` on `NuclearEnergy`
  - `3254181` `ethan_salt_hiqb3_nq` on `normal`
- the retained endpoints below remain the bounded checkpoint snapshot, not the
  final campaign endpoint

Checkpoint retained endpoints and representative windows:

- Salt 2 high-Q:
  - latest retained time: `4914 s`
  - representative saved times: `4895-4914 s` (`20` saved times)
- Salt 3 high-Q:
  - latest retained time: `2966 s`
  - representative saved times: `2947-2966 s` (`20` saved times)
- Salt 4 high-Q:
  - latest retained time: `6191 s`
  - representative saved times: `6172-6191 s` (`20` saved times)
- Salt 2 low-Q:
  - latest retained time: `4886 s`
  - representative saved times: `4867-4886 s` (`20` saved times)
- Salt 3 low-Q:
  - latest retained time: `2972 s`
  - representative saved times: `2953-2972 s` (`20` saved times)
- Salt 4 low-Q:
  - latest retained time: `6197 s`
  - representative saved times: `6178-6197 s` (`20` saved times)

Taken together with the frozen Salt continuation wave, Salt 2-4 now each have
at least `20` representative retained saved times in all currently frozen
lanes.
