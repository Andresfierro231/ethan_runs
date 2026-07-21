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

- The present readable `Fluid` campaign is still the legacy readable surface
  rather than a new `v2` rerun.
- The external `Fluid` repo now carries a parallel `v2` bundle, campaign, and
  test path, but there are not yet readable `v2` diagnostics on disk.
- It is already useful for quantifying current 1D error trends and showing
  which closure family currently helps.
- It is not broad enough yet to defend one shared direct internal HTC closure
  over all Salt branches or cases.

## External refresh status

- Tracked bundle root:
  `ethan_cfd_informed_salt_v2`
- Tracked bundle generated on:
  `2026-06-29`
- Audited `v1` token occurrences across the loader/config/test surface:
  `16`
- Audited `v2` token occurrences across the loader/config/test surface:
  `38`
- Tracked `v2` readable-results root present:
  `False`
- Refresh status rows:
- `parallel_v2_bundle_published` [resolved]: bundle_root=ethan_cfd_informed_salt_v2; generated_on=2026-06-29. Next: keep the v2 snapshot as the tracked parallel contract until a later replacement is intentionally published.
- `v2_loader_config_test_wiring_present` [resolved]: tracked v2 token occurrences across audited files=38. Next: preserve the parallel v1 path but keep new tracked Ethan CFD-informed runs pointed at the v2 mode.
- `reproducible_v2_bundle_producer_present` [resolved]: producer_path=/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/tools/build_ethan_cfd_informed_salt_v2_bundle.py. Next: use the producer script to rebuild the tracked static bundle whenever the local Ethan closure contract changes.
- `readable_v2_diagnostics_present` [open]: results_root_exists=True; readable_results_present=False; results_root=/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/ethan_cfd_informed_salt_v2. Next: run the bounded ethan_cfd_informed_salt_v2 campaign and publish readable status rows under results/diagnostics.
- `refreshed_surface_tables_still_carried_from_v1` [open]: tracked v2 snapshot still carries descriptor and safe-subset surface tables forward unchanged from v1. Next: land the dedicated refreshed surface-table producer before claiming a fully regenerated v2 closure surface.
