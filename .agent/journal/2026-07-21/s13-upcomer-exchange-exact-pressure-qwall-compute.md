---
provenance:
  - tools/extract/build_s13_upcomer_exchange_exact_pressure_qwall_compute.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/trusted_wall_Q_wall_summary.csv
tags: [s13, upcomer-exchange, exact-field-reduction, pressure, wallHeatFlux]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-EXACT-PRESSURE-QWALL-COMPUTE-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute.json
task: TODO-S13-UPCOMER-EXCHANGE-EXACT-PRESSURE-QWALL-COMPUTE-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
---
# S13 Exact Pressure and Qwall Compute

## Attempted

Implemented a read-only native-field reducer for Salt2/Salt3/Salt4 S13 target
windows. The reducer maps selected global cell IDs through `cellProcAddressing`
to sample `p` and `p_rgh`, and maps trusted-wall global face IDs through
`faceProcAddressing` plus processor `boundary` metadata to integrate
`wallHeatFlux`.

## Observed

Exact target-window native files exist for all three cases:

- Salt2 at `7915`
- Salt3 at `7618`
- Salt4 at `10000`

The pressure reductions produced one released row per case. Trusted-wall
wallHeatFlux coverage is complete for `38880/38880` faces per case and
`0.063435001093 m2` per case.

`Q_wall_W`, positive into the seeded recirculation fluid, is:

- Salt2: `23.1161370708 W`
- Salt3: `25.3465488205 W`
- Salt4: `28.1231837021 W`

Each case has three trusted-wall faces whose native processor patch label is an
NCC seam label while the seeded face map labels the adjacent wall patch. Only
one of those carries nonzero flux per case, with absolute contribution below
`1e-3 W` and relative contribution about `2.57e-05` of the native integral.

## Inferred

The exact `Q_wall_W` blocker is unlocked for the seeded trusted-wall QOI. The
small NCC seam-label discrepancy is a geometry-label audit item, not missing
heat flux, because the global face-id mapping and area coverage are complete.

The pressure basis is also unlocked for the same seeded target windows. This
does not by itself release production harvest or same-QOI UQ.

## Caveats

The sign convention is explicit: OpenFOAM wallHeatFlux is retained as native
outward wall-normal sign, and `Q_wall_W = -sum(wallHeatFlux_i A_i)` so positive
`Q_wall_W` adds heat to the seeded fluid.

No heat residual was moved into internal `Nu`.

## Next Useful Actions

Refresh the sampler manifest from this exact pressure/Qwall package, then run a
separate same-QOI UQ preparation row for neighbor-window and mesh/GCI support.
Production harvest/admission should remain closed until those gates pass.
