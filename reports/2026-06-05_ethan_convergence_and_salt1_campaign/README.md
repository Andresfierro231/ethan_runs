# Ethan Eight-Case Convergence And Salt 1 Campaign

Generated: `2026-06-07T15:15:48-05:00`

## Method

- Salt representatives use the current best-supported row for each physical salt test, not both Jin and Kirst simultaneously, so the report stays at the requested eight study cases.
- Water cases are reclassified with the same practical-steadiness ingredients used for the salt audit: final `|total_Q|` relative to heater power, late-window mdot drift, and late-window probe drift.
- Interpretation rule used here:
  - `essentially_steady`: final `|total_Q|/heater < 1%` and no noticeable late-window drift.
  - `borderline_but_usable`: residual is small, but mdot or probe drift is still noticeable.
  - `not_steady_enough`: residual remains too large for a clean steady-state claim.

## Eight-case determination

- `Salt 1` (`viscosity_screening_salt_test_1_kirst_coarse_mesh`): `not_steady_enough`. case may look flat, but residual heat-balance floor or late-window drift remains too large for a clean steady-state claim
- `Salt 2` (`val_salt_test_2_coarse_mesh_laminar`): `essentially_steady`. late-window drift is tiny and net heat-balance residual is below 0.5% of heater power; active continuation is still running, so this is usable now but still worth refreshing later
- `Salt 3` (`viscosity_screening_salt_test_3_jin_coarse_mesh`): `essentially_steady`. late-window drift is tiny and net heat-balance residual is below 0.5% of heater power
- `Salt 4` (`viscosity_screening_salt_test_4_jin_coarse_mesh`): `borderline_but_usable`. tail is flat enough for practical use, but residual heat-balance floor is still noticeable
- `Water 1` (`val_water_test_1_coarse_mesh_laminar`): `borderline_but_usable`. Residual is small, but late-window drift is still noticeable.
- `Water 2` (`val_water_test_2_coarse_mesh_laminar`): `borderline_but_usable`. Residual is small, but late-window drift is still noticeable.
- `Water 3` (`val_water_test_3_coarse_mesh_laminar`): `borderline_but_usable`. Residual is small, but late-window drift is still noticeable.
- `Water 4` (`val_water_test_4_coarse_mesh_laminar`): `borderline_but_usable`. Residual is small, but late-window drift is still noticeable.

## Salt 1 targeted campaign hypotheses

- `Salt 1 primarily needs a longer continuation with the repaired MPI bootstrap.`: Continue Salt 1 Jin from 3229 s and Salt 1 Kirst from 3279.163522013 s with the corrected OpenFOAM bootstrap. Expected signal: If the 4% net-Q floor is mostly a runtime issue, the residual should fall materially without a large setup change.
- `Salt 1 is a low-power modeling problem, not only a runtime problem.`: Only after the continuation retries finish, test a targeted Salt 1 loss-model or cooler-h sensitivity rather than a blanket property sweep. Expected signal: If the residual floor survives the new continuation, the setup itself is the next lever, not more runtime alone.

## Recommended Salt 1 tries

- Try 1: Salt 1 Jin continuation retry with the repaired OpenFOAM MPI bootstrap.
- Try 2: Salt 1 Kirst continuation retry with the same repaired bootstrap, because it already reached the coded convergence monitor but still has an unacceptably large residual floor.

## Output files

- `eight_case_convergence_summary.csv`: main determination table.
- `salt1_hypothesis_matrix.csv`: Salt 1 targeted hypothesis table.
- `figures/png/eight_case_convergence_dashboard.png`: residual-versus-mdot-drift convergence dashboard.

