# Parser/API Contract

## Input Schema

The parser consumes the repo-local CSV schema represented by:

- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv`

Required source fields for predictive passive external rows:

- `case_id`
- `segment_id`
- `patch_group`
- `physical_role`
- `mode`
- `convection_active`
- `radiation_active`
- `layer_resistance_active`
- `h_W_m2_K`
- `Ta_K`
- `Tsur_K`
- `emissivity`
- `area_m2`
- `coverage_factor`
- `wall_layer_resistance_status`
- `drive_temperature_selector`
- `radiation_policy`
- `source_use_category`
- `runtime_heat_flux_policy`
- `runtime_temperature_policy`
- `residual_policy`
- `source_paths`

## Fluid API Shape

Suggested public dataclass in
`tamu_loop_model_v2/external_boundary.py`:

```python
@dataclass(frozen=True)
class ExternalBoundaryRecord:
    case_id: str
    segment_id: str
    patch_group: str
    physical_role: str
    mode: str
    convection_active: bool
    radiation_active: bool
    layer_resistance_active: bool
    h_W_m2_K: Optional[float]
    Ta_K: Optional[float]
    Tsur_K: Optional[float]
    emissivity: Optional[float]
    area_m2: Optional[float]
    coverage_factor: float
    wall_layer_resistance_status: str
    drive_temperature_selector: str
    radiation_policy: str
    source_use_category: str
    runtime_heat_flux_policy: str
    runtime_temperature_policy: str
    residual_policy: str
    source_paths: str
```

Suggested conversion output for `ScenarioConfig.external_boundary_role_rows`:

```python
{
    "parent_segment": "left_upper_vertical",
    "source_case_id": "salt_2",
    "source_segment_id": "upcomer",
    "patch_group": "ambient_wall",
    "role": "ambient_wall",
    "mode": "predictive",
    "h_W_m2K": 3.703887805,
    "area_m2": 0.050313118,
    "Ta_K": 299.19,
    "Tsur_K": 299.19,
    "emissivity": 0.95,
    "coverage_multiplier": 1.0,
    "drive_selector": "fluid_segment_bulk_temperature_for_v1_setup_mode",
    "radiation_policy": "predictive_radiation_from_emissivity_Tsur",
    "source_paths": "..."
}
```

## Runtime Rejections

Reject any predictive row or scenario-loaded dictionary that includes or implies:

- realized CFD `wallHeatFlux` as a runtime value
- CFD `mdot` or CFD velocity as a runtime shortcut
- validation `TP` or `TW` temperatures as boundary or drive temperatures
- imposed CFD cooler duty in predictive mode
- residual heat used to fill missing `h`, `Ta`, `Tsur`, emissivity, area, wall/layer resistance, or internal `Nu`
- replay total heat plus separate predictive radiation/convection for the same row

## Mode Handling

- `predictive`: convert only setup fields into role rows.
- `replay`: parse for audit only; do not feed predictive role rows.
- `diagnostic_sensitivity`: parse for audit only unless a future row explicitly claims sensitivity execution.
- `blocked_missing_fields` and `document_only_source_sink_or_blocked`: retain in audit output and skip predictive role-row conversion.

## Segment Mapping

The parser must require an explicit mapping from `segment_id` to Fluid
`parent_segment` names. Do not silently guess from names. The starter mapping in
`segment_mapping_contract.csv` is a proposed default and must be reviewed by
Phase C before use.
