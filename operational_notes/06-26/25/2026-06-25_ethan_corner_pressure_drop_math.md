# Corner Pressure Drop Math

Date: `2026-06-25`
Task: `AGENT-131`

## Goal

Explain the math used for the new corner-pressure-drop table in a way that is
directly tied to the preserved case-analysis artifacts.

## Data source

The table uses existing case-analysis files named:

`feature_minor_loss_timeseries.csv`

Those rows were already produced from area-averaged endpoint patch reductions
on named loop features such as:

- `corner_lower_left`
- `corner_lower_right`
- `corner_upper_right`
- `corner_upper_left`

The current summarizer does not reconstruct any new OpenFOAM fields. It only
aggregates the preserved per-time rows.

## Why `p_rgh`

The preserved `p_rgh` field is the hydrostatic-corrected pressure-like field.
For this loop, that is the direct field we want when the question is frictional
or feature-local pressure loss rather than total static pressure including
vertical hydrostatic head.

The practical consequence is:

- use `p_rgh` for the corrected corner endpoint comparison
- keep raw `p` only as supporting context

## Per-time corner quantities

For one retained time `t` and one corner feature with a defined start patch and
end patch:

- `p_before_rgh(t) = start_p_rgh_pa`
- `p_after_rgh(t) = end_p_rgh_pa`
- `delta_p_rgh(t) = p_after_rgh(t) - p_before_rgh(t)`
- `pressure_drop_start_to_end_rgh(t) = p_before_rgh(t) - p_after_rgh(t)`

The preserved extractor stores:

- `start_p_rgh_pa`
- `end_p_rgh_pa`
- `delta_p_rgh_pa = end_p_rgh_pa - start_p_rgh_pa`
- `abs_delta_p_rgh_pa = |delta_p_rgh_pa|`

So the start-to-end pressure-drop sign convention used in the summary is just:

`pressure_drop_start_to_end_rgh_pa = -delta_p_rgh_pa`

## Windowed averages

For the last `N` available retained times for one case and one corner:

- `mean_start_p_rgh_pa = average(start_p_rgh_pa(t))`
- `mean_end_p_rgh_pa = average(end_p_rgh_pa(t))`
- `mean_delta_p_rgh_pa = average(delta_p_rgh_pa(t))`
- `mean_pressure_drop_start_to_end_rgh_pa = average(start_p_rgh_pa(t) - end_p_rgh_pa(t))`
- `mean_abs_delta_p_rgh_pa = average(|delta_p_rgh_pa(t)|)`

The summary table keeps both `mean_delta_p_rgh_pa` and
`mean_pressure_drop_start_to_end_rgh_pa` so the sign convention stays explicit.

## Important limitation

This method is an endpoint-pressure comparison across the named feature patches.
It is not yet a full feature-path hydro integral or a new cellwise path
integration. That limitation is already consistent with the repo’s existing
feature-pressure workflow.

## Current table availability

The current generated table uses the selected case-analysis roots under:

`tmp/2026-06-18_overnight_analysis_queue/case_analysis`

Observed retained-time availability in those selected roots:

- `13` source IDs selected
- `2` cases selected from `*_window20` roots
- `11` cases selected from `*_window12` roots
- actual available pressure-feature times in the selected CSVs are only `4` or
  `5` per case

So in the current output package:

- the `5`-step window is the only truly distinct averaging window
- the `10`- and `20`-step summaries collapse to the same retained rows because
  those additional times are not present in the selected corner-pressure CSVs
