# Ethan Fluid Replay Against Frozen State

Generated: `2026-06-22`

## Scope

- This package compares the current readable `Fluid` Salt replay against the
  June 22 frozen-state CFD contract.
- It does **not** assume straight sections are automatically fully developed.
- It keeps the current branch boundary explicit:
  - direct internal `Nu` is defended only on `left_lower_leg`
  - `upcomer` remains sensitivity-only
  - `right_leg` or downcomer remains blocked for direct `Nu`

## Best current readable 1D rows

Salt 1: ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_0 (|dT_air|=14.01 K, |dm_dot|=0.50%); Salt 2: ethan_cfd_informed_salt_baseline_ins_1.0in_rad_0 (|dT_air|=8.69 K, |dm_dot|=15.91%); Salt 3: ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1 (|dT_air|=22.75 K, |dm_dot|=8.91%); Salt 4: ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1 (|dT_air|=26.37 K, |dm_dot|=9.79%)

## Coverage boundary

- Readable hybrid scenarios: 3 condition rows, but only 3 total case rows.
- Conditions with incomplete baseline-vs-hybrid case coverage:
  `ins_1.0in_rad_0, ins_1.0in_rad_1, ins_2.0in_rad_1`.
- This is the practical meaning of the current domain-breadth gap:
  the hybrid closure family is not yet readable across the same Salt case set as
  the baseline family, so broad closure conclusions remain under-supported.

## Branch modeling boundary

- Upcomer:
  Derived sensitivity-only branch; model separately from the straight direct branches and consider a convection-cell style closure coupled to the loop state.
- Downcomer:
  Downcomer return branch remains blocked for direct Nu; cooler-adjacent return observables are still missing.

## Current interpretation

- The present readable `Fluid` campaign is still a pre-refresh reference
  surface rather than a new June 22 rerun.
- It is already useful for quantifying current 1D error trends and showing
  which closure family currently helps.
- It is not broad enough yet to defend one shared direct internal HTC closure
  over all Salt branches or cases.
- The exact blocker is now known: the external `Fluid` repo still reads the
  June 19 `ethan_cfd_informed_salt_v1` validation bundle, and there is no
  current producer in that repo to rebuild a refreshed Ethan CFD-informed Salt
  bundle from the June 22 closure/report roots.
