# Reconstructed T Repair Trial

Task: `AGENT-267`

Generated: `2026-07-13T13:06:25-05:00`

This package tests fresh reconstructed-`T` paths for Salt2 refined thermal
sampling without mutating native solver outputs. The `T` scan separates
whole-file scalar syntax/nonfinite checks from Kelvin plausibility checks,
because OpenFOAM boundary dictionaries can store auxiliary non-temperature
scalars such as `qConv`, `refGradient`, `valueFraction`, `h`, and `Q` in the
same `T` file.

## Decision

Repair smoke passed for requested cases: clean reconstructed T, successful temperature section sampling, and segment thermal extraction completed. Closure admission still requires review gates.

Final smoke scope: Salt2 refined `medium` at time `518`. The fine refined case
remains the next split-reconstruction target before mesh-family thermal
interpretation.

Computed medium segment rows:

- `lower_leg`: `HTC=457.3425559 W/m2/K`, `UA'=40.04991997 W/m/K`; direct Nu not admitted on this span.
- `upcomer`: `HTC=77.93723958 W/m2/K`, `UA'=6.691894684 W/m/K`, `Nu=4.284836461`.
- `downcomer`: still `thermally_blocked_segment_right_leg`.

## Key Outputs

- `summary.json`
- `outputs/reconstruction_trials.csv`
- `outputs/<level>/section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.csv`
- `outputs/<level>/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv` when the thermal smoke ran

## Boundary

These are repair-trial outputs. They are not closure-fit admissions by
themselves; the next step is review against heat-balance, sign, and mesh-family
admission gates.
