# Heat Enthalpy Interface Follow-up Task

Date: `2026-07-08`
Task: `AGENT-215`
Role: Coordinator / Writer

## Purpose

Open the follow-up heat task requested by the user: extract enthalpy-flow changes
at physical segment interfaces and populate residual columns in a new patchwise
heat-ledger package, without editing the July 8 wall-flux foundation package in
place.

## Coordination Decision

I added `TODO-HEAT-ENTHALPY-INTERFACE-LEDGER` to the Planned / Unclaimed queue.
The future worker is assigned a new package root:

`work_products/<date>_patchwise_heat_ledger_enthalpy_interfaces/**`

The existing foundation package remains read-only:

`work_products/2026-07-08_patchwise_heat_ledger/**`

## Observed Facts

- `work_products/2026-07-08_patchwise_heat_ledger/README.md` reports a 24-row
  Salt 2/3/4 Jin patchwise ledger with heater, cooler, ambient-wall, test-section,
  and junction groups.
- That package already carries bracketed-span `enthalpy_change_W` and
  `wallHeatFlux_vs_enthalpy_residual_W` using
  `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`.
- The span endpoint source is not the same as a complete physical segment
  interface extraction. It samples six span endpoints and states that cooler
  endpoints bracket only about 45-51% of cooler removal.
- Upcomer endpoint temperatures are strongly recirculation-contaminated
  according to the source README: 85-98% recirculation at endpoint cut planes.
- Junction rows in the thermal boundary contract are not bracketed by endpoint
  enthalpy stations.
- Current radiation treatment is metadata-only because no OpenFOAM `qr` output
  term was found in the July 8 artifacts.

## Inferred Interpretation

The original enthalpy blocker has evolved. The July 8 foundation package now has
a useful first enthalpy-residual layer, but it is not yet the final mechanistic
heat ledger needed for paper-grade closure. The next improvement should make the
control-volume boundaries explicit: inlet/outlet interface, patch-to-segment
mapping, mdot/cp provenance, recirculation validity, junction handling, and
resistance-network status.

## Blockers

- Physical segment interface surfaces must be inventoried or sampled before a
  full enthalpy ledger can be defended.
- Junction heat loss/gain remains a wall-flux grouping unless the junction
  control volumes are bracketed by flow interfaces.
- Upcomer residuals should remain diagnostic-only unless the extraction method
  explicitly handles reversing or multi-stream flow.
- The complete resistance network still requires defensible internal convection,
  wall conduction, external convection, and optional `qr` radiation terms.
- Current Salt evidence remains coarse mesh; mesh uncertainty is still a
  separate publication blocker.

## Exact Files Used

- `.agent/BOARD.md`
- `.agent/status/2026-07-08_AGENT-215.md`
- `.agent/journal/2026-07-08/heat-enthalpy-interface-followup-task.md`
- `journals/2026-07/2026-07-08_ethan_runs.md`
- `work_products/2026-07-08_patchwise_heat_ledger/README.md`
- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_span_endpoint_temperatures/README.md`
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`
- `work_products/2026-07-08_thermal_boundary_contract/README.md`
- `work_products/2026-07-08_thermal_boundary_contract/span_heat_residuals.csv`

## Recommended Next Action

Claim `TODO-HEAT-ENTHALPY-INTERFACE-LEDGER` and start with the interface
registry. The worker should prove which physical segments can be bracketed with
existing `secmeanSurfaces` data and which require new OpenFOAM sampling before
building `patchwise_heat_ledger_enthalpy_interfaces.csv`.
