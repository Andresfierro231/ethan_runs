# Ethan Blocker Report And Follow-On Wave

Generated: `2026-06-19`

Refreshed: `2026-06-22`

## Purpose

This package explains why the June 18 continuation wave was needed, turns the
remaining blocker set into a Salt-first 1D-model plan, and documents the next
bounded CFD wave that is safe to submit from the readable artifacts alone.

The June 22 refresh records the actual runtime outcomes after the first June 19
launches: two Salt 4 bracket jobs failed because their staged trees were
incomplete, and the packed optimum-insulation job failed because the
self-staging script depended on `rg` on the compute node. Those failures were
preserved, the launchers were hardened, and only the failed jobs were
relaunched.

## Why the current submitted continuations were needed

The June 18 continuation wave was justified by three immediate scientific
needs:

1. strengthen retained-time support on the existing Salt Jin and Water cases so
   the current closure packages are not forced to rely only on short, inherited
   late windows;
2. improve the chance of recovering defended last-window straight-section
   hydraulic rows for a true late-window sensitivity pass;
3. move Water from readiness-only interpretation toward an actual closure-gated
   dependency lane without inventing new scenario dimensions before the base
   cases stabilize.

The current closure-to-modeling handoff remains explicit that two blocker
classes still exist:

- feature `K_eff` needs a retained-time full-path hydro closure and cannot be
  fixed by proxy endpoint evidence alone;
- straight friction late-window sensitivity still needs retained-time defended
  hydro rows rather than only case-mean defended rows.

Those boundaries come from the June 19 v3 handoff and Salt dependency package,
not from guesswork.

## Blocker-first interpretation

### Blocker 1: retained-time feature-path hydro integrals for `K_eff`

- Current status: `not_defensible_yet`
- What is missing: retained-time feature-path density / hydro integrals beyond
  the preserved proxy endpoint `p_rgh` residual method
- Why more CFD alone is not enough: the readable additive artifact stack still
  does not preserve the pathwise integral needed to promote feature losses into
  a defended reduced-order closure

Practical implication:

- keep feature `K_eff` out of the first defended 1D model
- if this blocker becomes top priority, the next implementation task must be an
  upstream retained-time path extractor in addition to any more CFD runtime

### Blocker 2: retained-time defended straight-section hydro rows for the last-window pass

- Current status: straight friction is still `provisional_defended`
- What is missing: retained-time defended hydro-corrected straight rows for a
  true last-20-second sensitivity check
- Why the June 18 continuations were needed: more late-time writes on the
  existing Salt Jin and Water runs are the fastest way to improve that retained
  support without changing physics, mesh, or numerics

Practical implication:

- the ongoing continuation jobs remain the right blocker-first CFD action
- new scenario expansion should stay Salt-only and bounded until those base
  continuations mature further

## Salt-first 1D model plan

Build the first lightweight model in this order:

1. Use Salt only.
2. Use straight-section hydraulic closure first.
3. Carry thermal behavior with effective `UA'(x)` as the primary surface and
   effective `HTC(x)` as the secondary surface.
4. Admit direct Salt `Nu` only on the current limited domain.
5. Exclude feature `K_eff` and all Water dependency fits from the defended v1
   model.

### Admitted Salt closures today

- straight-section friction:
  - status: `provisional_defended`
  - model: `class_aware_re_power_law`
  - fit-used rows: `12`
  - active classes: `lower_leg`, `test_section_span`
- Salt `Nu`:
  - status: `provisional_defended`
  - model: `branch_aware_re_power_law`
  - fit-used rows: `7`
  - active direct branch: `left_lower_leg`
- Salt thermal state surface ranking:
  - primary: `UA'(x)`
  - secondary: `HTC(x)`
  - supporting-only: branch-averaged `R'_th`
  - diagnostic-only: profile `R'_th(x)`

### Explicit v1 exclusions

- feature `K_eff`
- Water dependency fits
- `right_leg` Salt thermal closure
- derived `upcomer` as a defended fitted `Nu` surface

## Best next CFD runs

### What not to submit from the readable artifacts

Do not submit the June 18 cooler-`h` DOE literally as written.

The readable setup-modeling evidence shows that the governing cooler branch in
`0/T` is a fixed negative `Q` sink, not a live cooler-side convective `h`
control. Metadata preserves a nominal cooler `h`, but the transformation from
that metadata field to the readable fixed-sink branch is not visible in the
workspace artifacts.

That means a direct cooler-`h` mutation would not be reproducible from the
readable files alone.

### Submitted bounded next wave

The safe follow-on wave therefore uses only visible, traceable controls:

- lower-heater patch `Q`
- outer insulation thickness

The selected cases are:

- Salt 2 Jin
- Salt 4 Jin

They were chosen because:

- both already contribute defended Salt fit rows;
- Salt 2 remains the validation anchor and lower-Re / lower-power side of the
  defended Salt domain;
- Salt 4 remains the hotter, higher-Re edge of the defended Salt domain;
- Salt 1 does not currently contribute defended fit rows;
- Salt 3 is useful but can wait behind the first bracketed wave.

The submitted child mutations are:

- `+10%` lower-heater `Q` and `+0.40 in` outer insulation
- `-10%` lower-heater `Q` and `-0.40 in` outer insulation

for each of:

- Salt 2 Jin
- Salt 4 Jin

Water is deliberately excluded from this new scenario wave. Water still needs
closure hardening on existing cases before new scenario expansion is justified.

## June 22 repair record

### Diagnosed June 19 failures

- `3246562` `ethan_s4j_hiqins`
  - failed in `00:00:10`
  - staged child was missing `system/controlDict`
- `3246563` `ethan_s4j_loqins`
  - failed in `00:00:10`
  - staged child was missing `system/controlDict`
- `3246927` `ethan_salt_optpack`
  - failed in `00:36:33`
  - compute-node self-staging script depended on `rg`, which was not available
    on the runtime path

The failed case trees were preserved under `failed_stage_preserved/` rather
than overwritten.

### Repair actions

- hardened the generic continuation launcher to reject missing `0/`,
  `constant/`, `system/`, or `system/controlDict` before `foamRun`
- replaced the optimum staging script `rg` checks with `grep -Eq`
- rebuilt both Salt 4 bracket children from the static Salt 4 continuation
  source and then re-applied only the intended mutated `0/T` and
  `case_config.yaml` files
- switched the repaired optimum relaunch to the local pre-staged packed
  launcher instead of the earlier compute-node self-staging path

### Relaunch IDs

- repaired Salt 4 high-Q / high-insulation child:
  - `3250524` `ethan_s4j_hiqins_r2`
- repaired Salt 4 low-Q / low-insulation child:
  - `3250525` `ethan_s4j_loqins_r2`
- repaired packed optimum-thickness wave:
  - `3250526` `ethan_salt_optpack`

## Queue state on 2026-06-22

Observed from `squeue` and `sacct` on `2026-06-22`:

- running:
  - `3244950` `ethan_s3j_cont`
  - `3244951` `ethan_s2j_cont`
  - `3244954` `ethan_s4j_cont`
  - `3244957` `ethan_w2_cont`
  - `3246561` `ethan_s2j_hiqins`
  - `3246564` `ethan_s2j_loqins`
  - `3250524` `ethan_s4j_hiqins_r2`
  - `3250525` `ethan_s4j_loqins_r2`
- pending:
  - `3250526` `ethan_salt_optpack`
- failed:
  - `3246562` `ethan_s4j_hiqins`
  - `3246563` `ethan_s4j_loqins`
  - `3246927` `ethan_salt_optpack`
- timed out:
  - `3244952` `ethan_w3_cont`
  - `3244953` `ethan_w1_cont`
  - `3244956` `ethan_w4_cont`
- completed:
  - `3244955` `ethan_s1j_cont`

Those June 22 Water timeouts reinforce the existing bounded Water-readiness
interpretation, but they do not change the defended Salt-only modeling boundary
defined elsewhere in this package.

## Artifacts

- `blocker_queue.csv`
- `blocker_resolution_plan.md`
- `one_d_model_steps.csv`
- `one_d_implementation_spec.md`
- `one_d_state_vector.csv`
- `one_d_closure_map.csv`
- `one_d_calibration_table_spec.csv`
- `run_recommendations.csv`
- `summary.json`
