# Pressure Decomposition Misunderstanding And Slide Fix

Date: 2026-07-09  
Task: AGENT-232

## What Was Misleading

The original pressure-decomposition slide used
`pressure_decomposition_by_span.svg` as the main figure. That figure mixed
irreversible mechanical loss bars with signed `p_rgh` density-gradient source
terms. As an initial viewer, it was natural to read the large negative upper-leg
density-gradient bar as a large upper-leg pressure loss.

That interpretation is wrong.

The upper leg's mechanical friction target is ordinary-sized:

```text
Salt 2 upper_leg de-buoyed distributed friction: 6.708 Pa
Salt 3 upper_leg de-buoyed distributed friction: 6.717 Pa
Salt 4 upper_leg de-buoyed distributed friction: 6.762 Pa
```

The large upper-leg density-gradient value is a signed `p_rgh` cancellation
term:

```text
Salt 2 upper_leg gross p_rgh term:            +32.566 Pa
Salt 2 upper_leg density-gradient term:       -39.274 Pa
Salt 2 upper_leg combined p_rgh+density term:  -6.708 Pa
Salt 2 upper_leg mechanical friction target:   +6.708 Pa
```

It shows why raw `p_rgh` cannot be treated as friction. It does not mean the
upper leg dominates mechanical pressure loss.

## Geometry Direction Context

The physical loop directions matter:

- `right_leg` is the downcomer: flow goes downward with gravity.
- `left_lower_leg`, `test_section_span`, and `left_upper_leg` form the left-side
  riser/upcomer path: flow goes upward against gravity.
- `lower_leg` is the heater-side lower span.
- `upper_leg` is the cooler-side upper span.

The pressure reductions also have mesh station ordering and
`flow_orientation_sigma`. If station order and flow direction differ, a raw
start-to-end density or pressure difference can be physically misleading unless
it is projected along flow.

## Slide Fix

Slide 3 now uses this figure as the primary visual:

```text
work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/mechanical_pressure_terms_by_span.svg
```

This replacement figure excludes signed `p_rgh` density-gradient source terms
from the main slide and shows only loss-scale pressure terms:

- de-buoyed distributed friction target
- development/reset estimate
- minor-loss upper bound

July 9 readability update: the figure was changed from a crowded vertical
grouped-bar chart to a horizontal grouped-bar chart with one row per case/span.
The row labels use short span names such as `right/down`, `left lower`,
`test section`, and `left upper` to avoid overlapping text in the slide.

The original signed decomposition figure remains available as an optional
support figure:

```text
work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/pressure_decomposition_by_span.svg
```

Use the original only to make the method point:

```text
Raw p_rgh slopes are not friction in a non-isothermal buoyant loop.
```

Do not use it to compare which span has the largest mechanical pressure loss.

## Slide-Safe Interpretation

Use:

```text
Once the signed p_rgh density-gradient terms are separated, the mechanical
pressure-loss scale is comparable across the main legs. The upper leg's large
p_rgh cancellation term is not a large friction loss.
```

Avoid:

```text
The upper leg is responsible for the dominant pressure drop.
```

That statement confuses a signed `p_rgh` density-gradient cancellation with
irreversible mechanical loss.
