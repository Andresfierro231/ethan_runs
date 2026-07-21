# ROM Post-Processing Correctness Validation

Date: `2026-07-01`  
Task: `AGENT-165`  
Status: generated audit package from existing work products; no OpenFOAM run

## Purpose

This package implements the first reusable audit layer requested for the ROM and
post-processing work. It normalizes the existing mesh-geometry, pressure/friction,
and thermal closure outputs into tables that future agents can use for model-form
bakeoffs and correctness checks.

## Generated Tables

- `geometry_reference.csv`: mesh-derived station/tangent/bore plus section area,
  wetted perimeter, hydraulic diameter, fitting-end flag, and flow-alignment flag.
- `pressure_friction_audit.csv`: per-segment pressure/friction rows with an audit
  class stating whether the row is direct-friction candidate, apparent resistance,
  or not direct friction until variable-density buoyancy correction is added.
- `thermal_sign_identity_audit.csv`: per-segment thermal rows with the `UA' = hP`
  identity error and sign-convention audit class.
- `closure_observations.csv`: normalized long-form observation table for future
  ROM model-form bakeoffs.
- `model_form_specs_seed.json`: initial candidate model-form specs to score later.
- `resistance_taxonomy_catalog.json`: reusable definitions for hydraulic,
  buoyancy, development, recirculation, and thermal resistance classes.

The audit tables also carry the physical mental-model columns:
`resistance_class`, `physics_role`, `development_state`, `buoyancy_role`, and
`closure_admissibility`. Thermal rows carry `thermal_resistance_class`,
`rom_energy_role`, and `nu_admissibility`.

Work-product root: `work_products/2026-07-01_rom_postprocessing_correctness_validation`

## Counts

- Geometry rows: `90`
- Pressure/friction rows: `36`
- Thermal rows: `9`
- Closure-observation rows: `333`

Pressure audit classes:

- `diagnostic_static_or_secondary`: 18
- `direct_friction_candidate`: 6
- `not_direct_friction`: 12

Thermal audit classes:

- `identity_ok_sign_convention_needs_review`: 6
- `not_computed_thermally_blocked_segment_right_leg`: 3

Pressure resistance classes:

- `buoyancy_contaminated_apparent_resistance`: 12
- `distributed_wall_friction_candidate`: 6
- `reversible_acceleration_area_change_diagnostic`: 18

Thermal resistance classes:

- `recirculation_cell_effective_thermal_resistance`: 3
- `thermal_resistance_UAprime`: 3
- `thermal_resistance_unavailable`: 3

## Loop Resistance Mental Model

For the 1D ROM, the loop pressure balance should be interpreted as:

```text
buoyancy drive =
  distributed wall friction
+ minor losses from bends/reducers/junctions
+ flow-development or redevelopment losses
+ reversible acceleration / area-change pressure exchange
+ recirculation-cell effective resistance
+ unresolved residual and uncertainty
```

This package does not yet solve every term. Instead, it classifies each extracted
quantity by physical role so later closure fits do not mix different terms. In
particular, `p_rgh` gradients in heated or cooled non-isothermal legs can contain
local buoyancy-source terms, so those rows are marked as buoyancy-contaminated
apparent resistance until the mechanical-loss decomposition is implemented.

The energy-side analogue is:

```text
q' = UA' * (T_wall - T_bulk)
R'_thermal = 1 / UA'
Nu = h * D_h / k(T_bulk)
```

`UA'` is treated as the primary ROM thermal conductance per length. `Nu` remains
direct or diagnostic unless the row's domain and data support a real correlation.

## Interpretation

The current mesh-corrected pressure/friction table is intentionally conservative:
negative apparent friction or heated/cooled non-isothermal spans are not promoted
to closure-grade friction. They are marked for the next pressure decomposition
step: add the variable-density buoyancy correction before fitting distributed
Darcy losses.

The thermal table confirms the existing `UA' = h * wetted_perimeter` consistency
route and exposes rows whose solver-sign convention still needs explicit
paper-facing interpretation. The values remain coarse-mesh until GCI results
exist.

## Next Implementation Step

Add the actual buoyancy-corrected mechanical-loss calculation to the pressure
pipeline once AGENT-162's extractor ownership is clear. This package gives that
next step a stable output contract and acceptance surface.
