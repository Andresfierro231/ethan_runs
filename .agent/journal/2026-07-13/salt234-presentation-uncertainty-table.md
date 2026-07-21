# Salt2/3/4 Presentation Uncertainty Table

Date: `2026-07-13`
Task: `AGENT-273`
Role: Coordinator / Implementer / Tester / Writer

## Prompt

The user requested a compact next-presentation table for admitted Salt2/3/4:
mdot, key temperatures, wall temperature, and total_Q residual, with mean,
corrected SEM, oscillation amplitude, drift over 300 s, and verdict. They also
specified not to overuse relative error for total_Q because it is a near-zero
residual.

## Implementation

Extended `tools/analyze/build_time_series_uncertainty_story.py` to emit:

- `presentation_salt234_timeseries_uncertainty.csv`
- `presentation_salt234_timeseries_uncertainty.md`

The presentation rows are selected directly from AGENT-244
`steady_state_summary.csv` for current mainline Salt2/3/4 Jin continuations.
The table includes one mdot row, six probe-temperature rows, one wall
temperature row, and one total_Q residual row per case.

## Result

- Salt2/3/4 cases: `3`
- Quantities per case: `9`
- Presentation rows: `27`

The total_Q rows are retained even when their verdict is not steady, because
the requested presentation table should show the residual and its screen result:

- Salt2 total_Q: `not steady (drifting)`
- Salt3 total_Q: `not steady (drifting)`
- Salt4 total_Q: `steady`

No relative total_Q column is included; total_Q is reported as mean W, corrected
SEM W, detrended oscillation W, and drift over 300 s W.

## Validation

- `python3.11 -m py_compile tools/analyze/build_time_series_uncertainty_story.py tools/analyze/test_time_series_uncertainty_story.py`
- `python3.11 tools/analyze/test_time_series_uncertainty_story.py`
- `python3.11 tools/analyze/build_time_series_uncertainty_story.py`

## Boundaries

No solver outputs, registry files, scheduler state, or external Fluid files were
modified.
