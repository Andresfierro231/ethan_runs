# Coordinator / Writer Journal: PIV Slab Velocity Math

Date: `2026-06-25`
Task: `AGENT-132`

## Observed output

- Representative case `val_salt_test_2_coarse_mesh_laminar` defines
  `piv_slab_velocity` in:
  - `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/functions`
- The slab selection is defined in:
  - `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/topoSetDict`
- The runtime output header for that case is:
  - `Selection: piv_slab`
  - `Cells: 9240`
  - `Volume: 9.661896242e-06`
  - columns `volAverage(U)`, `volAverage(magU)`, `volAverage(T)`
- Cross-case `rg` checks show the same `piv_slab_magU` plus
  `piv_slab_velocity` pattern is used across the staged Salt and Water case
  trees.

## Interpretation

- The monitor is a pure OpenFOAM field-function-object reduction, not a custom
  postprocessor.
- The math is:
  - build scalar field `magU = |U|`
  - select `cellZone piv_slab`
  - compute volume averages of `U`, `magU`, and `T` over that zone
- This means the reported `magU` column is the volume average of local speed,
  `⟨|U|⟩`, not the norm of the average vector, `|⟨U⟩|`.

## Important boundary

- The comment in `system/functions` describes a later experimental-style mass
  flow surrogate `ṁ = ρ·⟨|U|⟩·πR²`, but that conversion is not performed by the
  `piv_slab_velocity` function object itself.
