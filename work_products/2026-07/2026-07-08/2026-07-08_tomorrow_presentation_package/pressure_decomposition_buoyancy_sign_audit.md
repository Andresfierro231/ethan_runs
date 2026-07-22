# Pressure Decomposition Buoyancy Sign Audit

Date: 2026-07-09  
Task: AGENT-230

## Why This Note Exists

While reviewing the presentation package, the lower-leg density-gradient
buoyancy sign was questioned. The concern was valid: the original summary chart
used the pressure-ledger `buoyancy_contribution_pa` column directly. That column
is in the ledger's station-order bookkeeping. For spans where flow runs opposite
the station order, especially `lower_leg`, this is not the along-flow signed
term a slide reader expects.

## Correction Made

`tools/analyze/build_postprocessor_summary_charts.py` now computes the plotted
value as:

```text
density_gradient_buoyancy_pa = gh_drho_dxi_pa_m * L_m
```

This is the flow-projected density-gradient term. The regenerated
`pressure_terms_summary.csv` also retains the old station-order value as
`station_order_buoyancy_pa` for traceability.

## Check Against Heater Physics

The lower leg is the heater leg. In the source momentum-budget data, flow is
opposite the mesh station order:

```text
lower_leg flow_orientation_sigma = -1
```

Therefore the station-order density increase corresponds to a density decrease
along actual flow. That is physically consistent with heating.

For Salt 2:

```text
station order rho: 1951.99 -> 1956.33 kg/m^3
flow direction rho: 1956.33 -> 1951.99 kg/m^3

old station_order_buoyancy_pa: +5.218 Pa
new flow-projected density_gradient_buoyancy_pa: -5.218 Pa
```

The upper leg keeps a negative sign because its station order and flow direction
agree in this reduction:

```text
Salt 2 upper_leg flow_orientation_sigma = +1
flow direction rho: 1955.08 -> 1959.92 kg/m^3
flow-projected density_gradient_buoyancy_pa: -39.274 Pa
```

## Interpretation

The density-gradient bar is not friction and should not be described as a
standalone pressure loss. It is a signed `p_rgh` momentum-balance term. Negative
values indicate a source/driver term in the flow-projected balance:

```text
friction_loss_per_volume = -d(p_rgh)/dxi - gh*d(rho)/dxi - rho*u*du/dxi
```

For the presentation, the safe wording is:

```text
The density-gradient term is flow-projected and signed. It demonstrates why raw
p_rgh slopes cannot be read as friction in heated/cooled legs. The mechanical
fit target remains the de-buoyed distributed-friction column.
```

## Files Updated

- `tools/analyze/build_postprocessor_summary_charts.py`
- `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/pressure_decomposition_by_span.svg`
- `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/tables/pressure_terms_summary.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md`
