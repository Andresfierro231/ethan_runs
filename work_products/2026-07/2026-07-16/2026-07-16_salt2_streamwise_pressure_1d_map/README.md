# AGENT-456 Salt2 Streamwise Pressure / 1D Map

## Purpose

Identify Salt2 average pressure values through the loop, label each CFD station by physical location, and map the CFD spans to the Fluid 1D model segments.

## Outputs

- `salt2_streamwise_pressure_1d_map.csv`: 30 station rows in loop-flow order.
- `salt2_branch_average_pressure_map.csv`: 6 CFD branch averages in loop-flow order.
- `salt2_loop_pressure_sequence.md`: readable branch and station tables.
- `source_manifest.csv`: source and guardrail references.
- `summary.json`: row counts and key labels.

## Key Mapping

- `lower_leg` = heater = Fluid `heated_incline`; flow order `s04 -> s00`.
- `right_leg` = downcomer = Fluid `right_vertical`; flow order `s00 -> s04`.
- `upper_leg` = cooled top leg = Fluid top/HX composite.
- Upcomer path = `left_lower_leg -> test_section_span -> left_upper_leg`.

## Admission

These are harvested station averages. They are diagnostic pressure-map values and remain `fit_eligible=no` for friction/minor-loss fitting.

## Summary

- Station rows: `30`
- Branch average rows: `6`
- Case key: `salt2_mainline`
- Time: `7915` s
