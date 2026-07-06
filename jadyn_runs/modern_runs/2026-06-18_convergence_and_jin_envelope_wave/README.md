# 2026-06-18 Convergence And Jin Envelope Wave

## Purpose

This campaign stages and submits the next 3-5 day OpenFOAM continuation wave
needed to strengthen the current Ethan 3D CFD evidence stack.

This wave has two linked goals:

1. close the largest current scientific weakness by extending the
   convergence-limited Salt Jin and Water cases;
2. prepare a Jin-only Salt-family envelope DOE that can later vary heater power,
   cooling-branch fixed `Q`, and insulation thickness without changing property model, mesh,
   numerics, or turbulence mode.

This directory is the campaign-local provenance root for the continuation wave.
It does not overwrite earlier continuation candidates.

## Locked decisions

- Salt DOE family: Jin only
- Water role in this wave: continuation / convergence only
- Salt 1 Jin minimum runtime target: 120 wall-clock hours
- Salt 2/3/4 Jin continuation target: 120 wall-clock hours
- Water 1-4 continuation target: 72 wall-clock hours
- Physics/numerics frozen in this wave:
  - laminar model
  - existing mesh
  - existing `fvSchemes`
  - existing `fvSolution`
  - existing decomposition
- DOE children are gated on at least one clean new parent write

## Current scientific motivation

The June 18 interpretation closure and follow-on screening packages show:

- Salt-only thermal claims are strongest on the safe subset
  `left_lower_leg`, `test_section_span`, `left_upper_leg`, `upcomer`.
- Water remains convergence-limited and supporting-only in several key branches.
- Cross-family hydraulics remain blocked from stronger claims.
- The next highest-value data improvement is more late-time support on the
  existing Salt Jin and Water runs, plus controlled Jin-only Salt envelope data.

## Heater / cooler / insulation mutation targets

The mutation path for the later Jin DOE is now identified from source
dictionaries and setup reports:

- `heater_power_W` maps to the three lower heater patches
  - `pipeleg_lower_04_straight`
  - `pipeleg_lower_05_straight`
  - `pipeleg_lower_06_straight`
- the powered test-section patch `pipeleg_left_04_test_section` is a separate
  `Q` boundary input and is not part of the case-level `heater_power_W`
  operating-point definition for this wave
- insulation thickness is controlled directly through `0/T`
- the readable cooler-side metadata field `bc_params.cooler.h` is not the live
  DOE knob in the current 3D cases because the authoritative cooling branch in
  `0/T` is still a fixed-`Q` surrogate
- any future cooler-side DOE in this family must therefore mutate the
  cooling-branch fixed sink patches in `0/T`, not just metadata `cooler h`

This wave documents those targets but does not submit DOE children until the
parent continuations produce at least one clean new write.

## Heat-balance contract for future DOE children

Current readable Ethan heat balance uses a mixed contract:

- lower-heater power is imposed explicitly through fixed `Q` heater patches
- the test-section power patch remains a separate explicit `Q` source in the
  salt family
- the cooling branch is an imposed fixed-`Q` sink on the cooler plus the two
  adjacent reducers
- the rest of the loop loses heat through temperature-dependent ambient-style
  wall surrogates

That means a future fixed-`Q` DOE child must not assume:

- `heater_power_W == cooling_power_W`
- or that metadata `bc_params.cooler.h` alone controls the real cooler-side
  removal

Instead, the child must record a parent late-window reference-state ledger and
enforce `Q_in - Q_lost ≈ 0`, with `Q_lost = Q_removed + Q_ambient` at that
reference state. Solve the cooling-branch fixed sink as the residual needed to
keep that relation near zero after the heater mutation. Use direct sectionwise
wall-heat totals for that bookkeeping. Do **not** add
`ambient_proxy_w` on top of full cooling removal because the ambient proxy
already includes cooling-branch excess bookkeeping.

Observed boundary from the current repo evidence:

- Salt 2 can show near-zero late-tail sectionwise closure in the existing
  preserved run (`net total = +0.241 W` at the cited late tail), but that is an
  observed runtime result, not a DOE staging invariant
- the current June 19 Salt bracket wave does **not** preserve a strict
  balance-by-construction contract because heater power changed while the
  cooling-branch fixed `Q` sinks stayed at the parent values

## Parent cases

See [campaign_manifest.csv](./campaign_manifest.csv) for the exact parent paths,
latest known restart times, walltime targets, and intended job names.

Salt 1 Jin and Salt 4 Jin use the most recent existing continuation candidates
as parent states. Salt 2 Jin, Salt 3 Jin, and Water 1-4 use the staged modern
run trees as parent states.

## Current queue refresh on 2026-06-22

- packed Salt continuation node:
  - job `3250777` `ethan_salt_contpack`
  - cases: `salt2_jin`, `salt3_jin`, `salt4_jin`
  - queue state: running
- packed Water continuation pilot:
  - job `3250776` `ethan_water_contpilot`
  - cases: `water1`, `water2`, `water3`, `water4`
  - queue state: running
- retention correction:
  - all active continuation cases in this wave now use `purgeWrite 21`
  - that is the storage-minimal setting that preserves the desired `20 s`
    late-window restart horizon at `writeInterval 1`
- layout change:
  - the short-lived standalone June 22 relaunch jobs `3250696`, `3250697`,
    `3250699`, and `3250700` were canceled after startup so the same work could
    be repacked onto two nodes instead of four
- scope note:
  - Salt 1 Jin was not included in the packed continuation relaunch; the Salt
    node intentionally trials the three currently prioritized Salt 2/3/4 cases
- pilot note:
  - inspect the Water `4 x 64` packed node first before copying that layout
    into other families or future scenario waves

## June 23 normal-queue follow-on

- current Water continuation pack:
  - job `3250776` `ethan_water_contpilot`
  - wall-clock runtime at cutover: about `22 h 09 m`
  - canceled on `2026-06-23 09:58 CDT` so the queued normal follow-on could
    become eligible
- queued `normal` follow-on:
  - job `3253879` `ethan_water_cont_nq`
  - queue state after cutover: pending on `Priority`
  - requested layout: `2` normal nodes, `256` total tasks, `48 h`
- why the follow-on uses `2` normal nodes instead of `1`:
  - `normal` nodes expose `128` CPUs each
  - the existing Water pilot keeps the defended `4 x 64` per-case packing
  - preserving that `64`-rank-per-case layout therefore needs `2` normal nodes
    rather than the single `256`-CPU dedicated node used by `NuclearEnergy`

## June 23 live-state check

Late-window `total_Q.dat` behavior says the Water pack is still mixed rather
than uniformly steady:

- Water 1 is near-flat over the last `4 s` but still drifting slightly upward
  (`+0.0067 W` over the last `4 s`)
- Water 2 still drifts negative (`-0.0102 W` over the last `4 s`)
- Water 3 still drifts negative (`-0.0107 W` over the last `4 s`)
- Water 4 is the least settled of the four (`-0.0355 W` over the last `4 s`)

So the Water continuation lane is still useful, but it is not yet a clean
all-cases steady-state endpoint.

## June 23 temporary checkpoint and recovery

- a bounded checkpoint snapshot was recorded on `2026-06-23` so the current
  retained windows could be analyzed without waiting for final convergence
- during that pass, the remaining Salt continuation node `3250777` and the
  queued normal Water follow-on `3253879` were canceled by mistake
- the user clarified that "freeze" meant "copy the latest retained window into
  a temporary analysis folder," not "stop the background jobs"
- the wave was therefore recovered immediately with:
  - `3254178` `ethan_salt_contpack` on `NuclearEnergy`
  - `3254180` `ethan_water_cont_nq` on `normal`
- the retained endpoints below remain the bounded checkpoint snapshot, not the
  final campaign endpoint
- the temporary Salt checkpoint copy is being written under
  `tmp/2026-06-23_salt_last20_checkpoint/`

Checkpoint retained endpoints and representative windows:

- Salt 2 continuation:
  - latest retained time: `5397 s`
  - representative saved times: `5378-5397 s` (`20` saved times)
- Salt 3 continuation:
  - latest retained time: `5286 s`
  - representative saved times: `5267-5286 s` (`20` saved times)
- Salt 4 continuation:
  - latest retained time: `8123 s`
  - representative saved times: `8104-8123 s` (`20` saved times)
- Water 1:
  - latest retained time: `8322 s`
  - representative saved times: `8303-8322 s` (`20` saved times)
- Water 2:
  - latest retained time: `6455 s`
  - representative saved times: `6436-6455 s` (`20` saved times)
- Water 3:
  - latest retained time: `5901 s`
  - representative saved times: `5882-5901 s` (`20` saved times)
- Water 4:
  - latest retained time: `4302 s`
  - representative saved times: `4283-4302 s` (`20` saved times)
- Salt 1 Jin reference lane:
  - latest retained time: `3756.33125 s`
  - retained saved times available: `18`
  - this lane falls short of the new `20`-step representative target

Water `4 x 64` packing assessment:

- operationally, no obvious overload signature appeared before freeze
- all four Water cases kept advancing and each preserved a full `20`-step
  representative retained window
- no OOM or node-failure signal appeared in Slurm accounting
- `foamRun` accounting for `3250776` reported `MaxRSS` roughly `0.65-0.73 GB`
  per lane and `MaxVMSize` roughly `5.26-5.34 GB`
- scientific caveat: operationally acceptable did not imply convergence, and
  Water 4 remained the least settled lane at freeze

## Timeline

### Day 1

- stage all 8 continuation copies
- submit 4 Salt Jin continuations and 4 Water continuations
- confirm bootstrap success and job queue state

### Day 2

- confirm first clean new writes where available
- classify any bootstrap/runtime failures
- if a parent has not yet produced a clean write, keep the DOE gated and record
  the fallback parent checkpoint

### Day 3

- first late-time convergence audit on any run with enough new writes
- classify each case as still transient, approaching steady, comparison-ready,
  or blocked

### Day 4

- update tracked monitoring notes
- identify which cases can support rebuilt late-window package reuse

### Day 5

- summarize Salt Jin continuation maturity
- summarize Water continuation maturity
- finalize the first go/no-go decision for Jin-only Salt envelope children

## Reproduction

Generic continuation wrapper:

- [scripts/run_continuation_generic_openfoam13.sbatch](./scripts/run_continuation_generic_openfoam13.sbatch)
- [scripts/run_packed_salt_continuation_wave.sbatch](./scripts/run_packed_salt_continuation_wave.sbatch)
- [scripts/run_packed_water_continuation_wave.sbatch](./scripts/run_packed_water_continuation_wave.sbatch)

Job submission uses `sbatch --parsable` with per-run `CASE_DIR`, `CASE_LABEL`,
`OPENFOAM13_ENV_SH`, and `RCWALLBC_LIBDIR` exports. Submitted job IDs are
recorded in the campaign manifest and the workspace journal/status files.

## Limitations

- This wave does not change numerics or turbulence mode.
- This wave does not repair the still-blocked cross-family hydraulic claim
  boundary by itself.
- DOE children remain gated until parent continuation health is demonstrated.
- Any future fixed-`Q` Salt DOE child should carry an explicit parent
  reference-state heat-balance note before submission.
