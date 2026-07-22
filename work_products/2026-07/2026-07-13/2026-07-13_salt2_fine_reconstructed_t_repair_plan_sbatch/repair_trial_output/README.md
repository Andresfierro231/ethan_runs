# Reconstructed T Repair Trial

Task: `AGENT-291`

Generated: `2026-07-13T16:05:17-05:00`

This package tests fresh reconstructed-`T` paths for Salt2 refined thermal
sampling without mutating native solver outputs. The `T` scan separates
whole-file scalar syntax/nonfinite checks from Kelvin plausibility checks,
because OpenFOAM boundary dictionaries can store auxiliary non-temperature
scalars such as `qConv`, `refGradient`, `valueFraction`, `h`, and `Q` in the
same `T` file.

## Decision

Repair smoke passed for requested cases: clean reconstructed T, successful temperature section sampling, and segment thermal extraction completed. Closure admission still requires review gates.

## Key Outputs

- `summary.json`
- `outputs/reconstruction_trials.csv`
- `outputs/<level>/section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.csv`
- `outputs/<level>/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv` when the thermal smoke ran

## Boundary

These are repair-trial outputs. They are not closure-fit admissions by
themselves; the next step is review against heat-balance, sign, and mesh-family
admission gates.
