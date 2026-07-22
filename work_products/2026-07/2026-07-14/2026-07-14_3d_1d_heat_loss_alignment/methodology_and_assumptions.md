# Methodology and Assumptions

## Objective

Track where heat enters and leaves the loop in Ethan's 3D CFD evidence and in
the current 1D fixed-mdot replay evidence, starting from the same setup
assumptions: same heater input places, same cooler removal place, and explicit
handling of passive wall/junction/radiation paths.

## Sign convention

All heat terms use the OpenFOAM/ledger convention used by the source packages:
positive heat enters the fluid and negative heat leaves the fluid. The output
tables split signed heat into source magnitude, loss magnitude, and net heat to
fluid so the sign cannot be hidden.

## Evidence lanes

`B3_imposed_setup_roles` is the closest current same-setup fixed-Q replay: it
maps imposed heater/test-section/cooler setup terms onto 1D segments.

`B2_realized_wallflux_roles` prescribes realized CFD wall flux by segment. It is
useful for locating where CFD actually transfers heat, but it is not a
predictive runtime model.

`N0`-`N3` radiation-off rows are retained as sensitivities only. They are useful
for role/lane diagnosis, but AGENT-277/287 showed that Ethan CFD
`rcExternalTemperature` includes emissivity/Tsur effects inside total
`wallHeatFlux`.

## Rigor gates

- Do not mutate native CFD outputs.
- Do not run heavy OpenFOAM from this package.
- Do not call radiation-off rows Ethan-CFD parity.
- Do not add separate 1D radiation on top of realized CFD `wallHeatFlux`.
- Do not use CFD mdot, realized CFD `wallHeatFlux`, or validation temperatures
  as setup-only forward-model runtime inputs.
- Report source paths for every table row.
- Report model-form/API blockers instead of fitting around them.

## Thesis use

This package supports a thesis/presentation section on heat-path attribution:
what the 3D model was asked to do, what heat it actually transferred at walls,
what the 1D replay can currently express, and which residuals belong to
heater, cooler/HX, passive wall, junction/storage, radiation metadata, or API
limitations.
