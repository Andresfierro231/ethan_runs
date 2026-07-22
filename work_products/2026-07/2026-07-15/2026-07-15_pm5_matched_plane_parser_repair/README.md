# PM5 Matched-Plane Parser Repair

Date: 2026-07-15
Task: AGENT-404

## Result

Repaired parsing of staged PM5 legacy VTK `FIELD attributes` arrays. The parser
recovers full `U`, `rho`, `T`, `Re`, `Pr`, `Ri`, `Gr`, `Ra`, and wall-band `T`
for `salt2_lo5q`.

The repair is partial: `salt2_hi5q`, `salt4_lo5q`, and `salt4_hi5q` staged
plane VTKs only contain `T`, `p_rgh`, and `U`, so F6 remains blocked until those
planes are resampled with `rho/Re/Pr/Ri/Gr/Ra`. Internal-Nu also remains blocked
because `wallHeatFlux` was not present in the staged wall-band VTKs.

## Outputs

- `repaired_pm5_matched_plane_metrics.csv` (12 rows)
- `pm5_f6_gate_refresh.csv` (3 rows)
- `pm5_resample_requirements.csv` (4 rows)
- `source_manifest.csv`
- `summary.json`

## Next Action

Resample the three incomplete PM5 cases with the full plane field set
`U rho T Re Pr Ri Gr Ra`, and repair the OpenFOAM `wallHeatFlux` generation
context before attempting internal-Nu admission.

## Guardrails

- No OpenFOAM solver or postprocessing launch.
- No native CFD solver-output mutation.
- No external Fluid edit.
- No scheduler action.
