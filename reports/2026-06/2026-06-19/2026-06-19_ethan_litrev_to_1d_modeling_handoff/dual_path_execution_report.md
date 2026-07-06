# Dual-Path Execution Report

Generated: `2026-06-19`

## Objective

Turn the current Salt CFD closure evidence into one shared ROM closure bundle
that can drive two implementation lanes:

1. the current `Fluid` solver in
   `../cfd-modeling-tools/tamu_first_order_model/Fluid/`
2. a new clean Salt-first skeleton named `salt_cfd_rom`

The first pass is CFD-only. Success means reproducing the admitted CFD-derived
closure behavior and the segment-level thermal/hydraulic state trends. It does
not yet require matching measured loop outputs.

## Start now, not later

The analysis can start immediately because the repo already has enough support
to define the first bundle boundary:

- explicit Salt property branches are required and already motivated by the
  June 2 discrepancy report
- straight distributed-friction support exists on the admitted Salt straights
- direct Salt `Nu(Re)` is defended on `left_lower_leg` only
- `UA'(x)` is the primary admitted thermal surface on the current safe subset
- `HTC(x)` is the secondary admitted thermal surface on the same subset
- the readable cooler forcing contract is fixed sink `Q`
- unresolved feature and return-path behavior can remain explicit residual
  buckets

What remains blocked is defended feature `K_eff`, not the entire ROM effort.

## Shared closure bundle

Both ROM paths should consume one identical imported bundle. The planned bundle
contract is published in `shared_closure_bundle_contract.csv`.

The required bundle contents are:

- explicit Salt material-branch selection contract
- straight friction fit for admitted straights
- direct `Nu(Re)` fit for `left_lower_leg`
- `UA'` surface library on the safe thermal subset
- `HTC` surface library on the same subset
- hydraulic residual policy
- thermal residual policy
- `K_eff` readiness table that preserves the blocker rather than inventing a
  defended coefficient

## Path A: Current `Fluid` solver

This is the first executable lane because the current solver already has:

- resumable campaign machinery
- diagnostics under `results/diagnostics/`
- profile-informed closure entrypoints
- existing contract tests for solver and calibration scaffolding

Relevant current entrypoints and anchors:

- `python -m tamu_loop_model_v2.run_profile_descriptor_diagnostics`
- `python -m tamu_loop_model_v2.run_joint_htc_friction_calibration`
- `python -m tamu_loop_model_v2.run_coupled_sectionwise_outer_closure`
- `make practical-reduced-order-plan`
- `results/diagnostics/practical_reduced_order_planning_2026-06-05_v1/REPORT.md`
- `results/diagnostics/profile_descriptor_diagnostics_weekend_salt1_ins1_rad1_v1/REPORT.md`
- `results/diagnostics/joint_htc_friction_calibration_weekend_focused_v1/trial_grid__salt.csv`

Recommended first implementation shape:

- do not reopen the baseline resumable predictive workflow first
- add a dedicated CFD-closure replay/import lane that reads one shared bundle
- keep the replay Salt-only in the first pass
- retain the existing finer mesh if useful, but map cells onto the admitted
  closure families from the seven-element v1 layout

Expected first-case set:

- `Salt 2 Val`
- `Salt 2 Jin`
- `Salt 2 Kirst`
- `Salt 3 Jin`
- `Salt 3 Kirst`
- `Salt 4 Jin`
- `Salt 4 Kirst`

Path-A rules:

- straight distributed friction may be direct on admitted straights
- direct `Nu(Re)` is allowed only on `left_lower_leg` and only inside the
  defended range
- `UA'` is primary and `HTC` is secondary
- feature `K_eff` stays out of defended closure logic
- unresolved hydraulics remain one explicit residual bucket
- unsupported thermal behavior remains one explicit thermal residual bucket

## Path B: `salt_cfd_rom`

`salt_cfd_rom` should be a new clean Salt-first ROM that consumes the same
shared bundle but avoids unrelated legacy solver surface area.

Recommended minimum topology:

1. `lower_leg_heater`
2. `test_section_span`
3. `left_lower_leg`
4. `left_upper_leg`
5. `upcomer`
6. `cooler_sink_bucket`
7. `unresolved_return_and_feature_bucket`

Recommended governing structure:

- one loop `mdot` balance from buoyancy versus admitted straight losses plus a
  hydraulic residual
- one thermal march using imposed heater `Q`, fixed cooler `Q`, `UA'` state
  surfaces, optional direct `Nu` on `left_lower_leg`, and a thermal residual
- explicit Salt property branch evaluation at each segment state

Path-B rules are intentionally the same as Path A on closure authority:

- no defended feature `K_eff`
- no Water lane in first pass
- no right-leg direct `Nu`
- no live cooler-side `h`

## Priority analysis stack

### 1. Straight friction

Promote one shared admitted straight-friction representation and keep the
literature baseline visible:

- baseline reference: `f_D = 64 / Re`
- current defended fit surface:
  `log(f_D) = 5.2316378122 - 0.9477837868 log(Re) + 2.9210668439 I[test_section_span]`
- use range from the June 19 implementation spec: approximately
  `80 <= Re <= 174`

### 2. Direct `Nu`

Keep direct `Nu` narrow and explicit:

- defended branch: `left_lower_leg`
- current defended form:
  `log(Nu) = -3.0042709988 + 0.9607621733 log(Re)`
- use range from the June 19 implementation spec: approximately
  `76 <= Re <= 166`

Everything else remains either `UA'`/`HTC` surface-driven or sensitivity-only.

### 3. `UA'` and `HTC`

Use `UA'` as the primary thermal state surface and `HTC` as the cross-check on:

- `left_lower_leg`
- `test_section_span`
- `left_upper_leg`
- `upcomer`

Do not back-compute defended `Nu` from unsupported branches and call it a new
closure law.

### 4. `K_eff`

Treat `K_eff` as readiness analysis only in this phase.

The blocker is exact and should remain visible:

- missing retained-time full-path hydro integrals
- current additive artifacts only support proxy-positive endpoint evidence
- more runtime alone does not resolve the blocker

### 5. Nondimensional gating

Use these as interpretation and promotion gates:

- `Re`
- `Pr`
- `Gz`
- `Gr`
- `Ra`
- `Ri`

Do not force a Salt/Water collapse in this phase.

## Test program

The ROM test matrix is published in `rom_test_matrix.csv`.

The intended order is:

1. shared bundle contract check
2. `Fluid` smoke replay on `Salt 2 Val` and `Salt 4 Jin`
3. `Fluid` full seven-case replay
4. `salt_cfd_rom` smoke replay on the same two anchor cases
5. `salt_cfd_rom` full seven-case replay
6. cross-path comparison using identical imported bundle contents

Acceptance rules:

- both paths must consume the same bundle manifest
- both paths must preserve the same closure authority boundary
- neither path may invent defended feature `K_eff`
- direct `Nu` must remain limited to the defended branch and range
- report outputs must expose residual usage rather than hiding it inside fitted
  friction or fitted `Nu`

## Small report outputs

The minimal human-facing report package for the future implementation pass
should include:

- imported correlation registry
- bundle manifest and provenance
- per-case replay scorecards for both paths
- cross-path comparison table
- explicit `K_eff` readiness note
- open-gaps table listing the exact CFD observables still missing

Within `ethan_runs`, the current package already serves as that planning and
evidence surface.

## Current stop boundary

This package implements the analysis/reporting side of the plan inside
`ethan_runs`.

Actual solver-code changes still belong in the 1D code workspace. When that
starts, this package should be treated as the authoritative report-side brief
for:

- what to implement first
- what correlations are allowed
- what to test
- what not to overclaim
