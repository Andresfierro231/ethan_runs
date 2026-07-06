# Ethan Pressure / HTC / Boundary-Layer Package

Generated: `2026-06-17`

This package is a new additive analysis layer built from the June 15 live
case-analysis artifacts. It covers `13` cases:

- Salt family: `9`
- Water family: `4`

The package is intentionally additive. It does **not** reopen the shared June
15/17 extraction scripts. Instead, it reuses the published raw CSV artifacts so
the new dissertation-facing pressure / HTC / boundary-layer report is
reproducible and non-destructive.

## What This Package Reports

- hydro-corrected straight-section pressure loss from `p` plus the explicit
  buoyancy integral
- `p_rgh` endpoint and integrated-gradient cross-checks
- section-local and loop-reference apparent Darcy factors
- core-only shear-based comparison on straight main pipes
- feature-level `K_eff` from the existing residual closure
- case-level pressure-head summaries, including wall `p`, wall `p_rgh`, and the
  wall hydro-head proxy range `p - p_rgh`
- bulk-vs-centerline temperature corrections
- fluid-side effective `h` and `Nu` fields from the azimuthal wall transport
  reductions
- section-level enthalpy balances
- first-pass hydraulic and thermal boundary-thickness ratios

## Primary Caveats

1. Pressure closure is strongest on straight repaired spans because those rows
   retain both wall-registered `p` / `p_rgh` and the tangent needed for the
   explicit buoyancy integral.
2. Feature `K_eff` is still based on the stored `p_rgh` residual closure. The
   raw package does not retain a dedicated feature-path density integral, so the
   additive package does not pretend to reconstruct one.
3. Salt-family HTC / Nu fields are compatible with the requested
   `rho*u*cp` bulk-temperature definition because `cp` is effectively constant
   in those cases.
4. Water-family HTC / Nu, enthalpy, and bulk-vs-centerline rows in this package
   now use an additive exact bulk-temperature rebuild from the preserved June 15
   cut-plane surfaces with water `rho(T)` and `cp(T)` polynomials. The package
   also preserves old-vs-new comparison tables so the method change is explicit.
5. Boundary-layer outputs remain first-pass landmark reductions. The
   representative profile figures are sparse landmark profile maps, not full
   circumferential field reconstructions.

## Key Artifacts

- `pressure_closure_by_section.csv`
- `pressure_closure_by_case.csv`
- `feature_keff_by_case.csv`
- `salt_side_htc_nu_fields.csv`
- `water_effective_htc_nu_fields.csv`
- `water_bulk_temperature_reweight_comparison.csv`
- `water_bulk_temperature_reweight_summary.csv`
- `fluid_side_htc_nu_section_summary.csv`
- `enthalpy_balance_by_leg.csv`
- `enthalpy_balance_by_case.csv`
- `bulk_vs_centerline_temperature_correction.csv`
- `boundary_layer_summary_by_section.csv`
- `representative_boundary_layer_profiles.csv`
- `representative_maps_index.csv`
- `MATH_COMPANION.md`

## High-Level Results

- straight-section rows reported: `78`
- feature rows reported: `65`
- maximum explicit straight-section pressure loss reported:
  `9604.96 Pa`
- maximum reported `K_eff`:
  `39.3909`

## Heat-Loss Separation TODO

This package does **not** collapse unresolved disagreement into salt-side
Nusselt. The following decomposition remains a follow-on:

- internal fluid-side convection
- wall conduction through the loop material and insulation stack
- external convection / radiation
- air-jacket `UA`

Those terms should be separated before any final nondimensional salt-side
correlation is treated as closure-ready.

## Figures

- pressure closure: `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/figures/png/pressure_closure_straight_sections.png`
- feature `K_eff`: `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/figures/png/feature_keff_by_case.png`
- bulk vs centerline correction: `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/figures/png/bulk_vs_centerline_correction.png`
- boundary-layer ratios: `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/figures/png/boundary_layer_ratio_family_summary.png`

## Summary JSON

Machine-readable package summary is in `summary.json`.
