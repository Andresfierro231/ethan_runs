---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/scientific_review.md
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/pressure_branch_scientific_review.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/junction_heat_loss_evidence_state.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/corner_pressure_drop_evidence_state.csv
tags: [scientific-review, pressure-map, junction-heat-loss, corner-pressure-drop]
related:
  - .agent/status/2026-07-16_AGENT-460.md
  - imports/2026-07-16_pressure_map_scientific_review_and_junction_corner_state.json
task: AGENT-460
date: 2026-07-16
role: Reviewer/Hydraulics/Thermal-modeling/Writer/Tester
type: journal
status: complete
---
# Pressure Map Scientific Review and Junction/Corner State

## Observed Output

AGENT-457 produced complete pressure-location maps across `11` harvested CFD
case keys (`330` station rows, `66` branch rows). AGENT-460 reviewed those rows
against the AGENT-449 pressure-ladder admission table and current heat/corner
evidence packages.

The pressure maps are internally coherent as maps:

- each case has the expected `30` station rows and `6` branch rows;
- `lower_leg` is consistently labeled heater / `heated_incline`;
- `right_leg` is consistently labeled downcomer / `right_vertical`;
- `upper_leg` is consistently labeled cooled top/HX composite.

## Interpretation

The pressure maps should not be promoted to hydraulic closure fits. AGENT-449
still blocks all `66` branch rows through the material recirculation mask, and
`24` branch rows have static-vs-`p_rgh` branch-delta sign differences. Absolute
static pressure is also gauge/reference sensitive and hydrostatic dominated, so
it is useful for location/state inspection but not a cross-case coefficient
metric.

For heat loss at junctions, we understand the aggregate realized heat loss:
Salt2/Salt3/Salt4 remove `39.128/43.235/48.485 W` from the fluid through the
`junction_other`/stub accounting lane. We do not yet have per-junction closure,
nor a predictive setup-only model; the evidence is based on realized total
`wallHeatFlux` with radiation embedded.

For corner pressure drops, we have identified and roughly quantified corners
from two-tap preserved feature rows. Mean apparent `K` values are about `8.269`
lower-left, `13.680` lower-right, `14.611` upper-right, and `6.382` upper-left.
After the available straight-loss proxy subtraction, mean local upper-bound `K`
values are about `3.453`, `7.096`, `6.973`, and `2.236`. These remain
diagnostic upper bounds because the tap length is only an `abs(dz)` proxy,
evidence is coarse/no-GCI, and recirculation affects adjacent upcomer rows.

## Next Gates

Pressure closure requires centerline-distance-normalized taps, accepted
straight-loss subtraction, low-recirculation masks, and mesh/GCI evidence.

Junction heat closure requires separating `junction_other` into the four
junction/stub surface groups and avoiding realized `wallHeatFlux` as a runtime
input.

Corner `K` admission requires full tap centerline lengths and mesh-refined/GCI
two-tap extraction.

## Validation

- `python3.11 -m unittest tools.analyze.test_pressure_map_scientific_review_and_junction_corner_state` passed `5/5`.
- `python3.11 tools/analyze/build_pressure_map_scientific_review_and_junction_corner_state.py` regenerated the package.
- JSON parse checks passed for the import manifest and generated summary.
