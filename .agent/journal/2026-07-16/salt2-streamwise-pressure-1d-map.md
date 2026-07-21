---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/station_pressure_ladder.csv
  - reference/geometry_reference.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/outputs_tamu_loop_v2_resumable/geometry/loop_segments.csv
  - work_products/2026-07/2026-07-16/2026-07-16_salt2_streamwise_pressure_1d_map/summary.json
tags: [salt2, pressure-ladder, streamwise-pressure, cfd-to-1d-map]
related:
  - .agent/status/2026-07-16_AGENT-456.md
  - imports/2026-07-16_salt2_streamwise_pressure_1d_map.json
task: AGENT-456
date: 2026-07-16
role: Hydraulics/Implementer/Tester/Writer
type: journal
status: complete
---
# Salt2 Streamwise Pressure / 1D Map

## Observed Output

The July 15 station pressure ladder contains `30` Salt2 mainline station rows at
`7915 s`. AGENT-456 filtered those rows and produced a loop-flow sequence plus
branch-average pressure table.

Branch arithmetic mean static pressures in loop-flow order:

| CFD span | Physical location | 1D map | mean p [Pa] | mean p_rgh [Pa] |
|---|---|---|---:|---:|
| `lower_leg` | heater / bottom heated incline | `heated_incline` | -6344.227 | 4.621 |
| `left_lower_leg` | lower upcomer below test section | `left_lower_vertical` | -3284.413 | -3.637 |
| `test_section_span` | test section / middle upcomer | `test_section` | -8629.364 | -2.372 |
| `left_upper_leg` | upper upcomer above test section | `left_upper_vertical` | -14453.701 | -3.735 |
| `upper_leg` | cooled leg / top cooled incline | Fluid top/HX composite | -7339.549 | -0.979 |
| `right_leg` | right downcomer / cold vertical return | `right_vertical` | -4409.427 | -2.632 |

## Interpretation

The critical naming correction is preserved in the generated columns:

- `lower_leg` is not the downcomer. It is the heater/bottom heated incline and
  maps to the 1D `heated_incline`.
- `right_leg` is not the heater. It is the right downcomer and maps to the 1D
  `right_vertical`.
- `upper_leg` is the cooled top path and maps to the Fluid top/HX composite,
  including `cooled_incline_hx_active`.

The station-level table includes both `mean_p_Pa` and `mean_p_rgh_Pa`. Use
`mean_p_Pa` as the static pressure value and retain `mean_p_rgh_Pa` as the
OpenFOAM gravity-adjusted pressure diagnostic. The rows are still diagnostic
because pressure-definition choice, straight-loss subtraction, recirculation
masking, and mesh/GCI admission are not all satisfied.

## Next Suggested Actions

Use `salt2_streamwise_pressure_1d_map.csv` as the Salt2 pressure-location map
for 1D comparison plots and pressure-budget review. Do not consume these rows
as admitted distributed `f_D` or component-`K` coefficients.

## Validation

- `python3.11 -m unittest tools.analyze.test_salt2_streamwise_pressure_1d_map` passed `5/5`.
- `python3.11 tools/analyze/build_salt2_streamwise_pressure_1d_map.py` regenerated the package.
- `python3.11 -m json.tool work_products/2026-07/2026-07-16/2026-07-16_salt2_streamwise_pressure_1d_map/summary.json` parsed successfully.

Generated docs index refresh was intentionally skipped because active AGENT-455
owns the generated `.agent` index files.
