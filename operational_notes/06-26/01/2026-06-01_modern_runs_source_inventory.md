# 2026-06-01 modern_runs source inventory

## Observed output

- Source tree inspected: `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs`
- Top-level campaign split:
  - `salt/`
  - `water/`
- Named case count in this snapshot:
  - `salt`: 8
  - `water`: 8
  - total: 16
- Reported external condition during this pass: a long-running `chmod` was
  still active, so permissions were expected to be in flux.

## Campaign structure

- `salt/` is a viscosity-screening batch over tests `1-4` with paired
  `jin` and `kirst` fluid-property variants.
- `water/` is a validation-model batch over tests `1-4` with paired
  `laminar` and `kOmegaSSTLM` model variants.

## Shared readable setup assumptions

- Common mesh and run controls across readable cases:
  - `mesh_group_id = 7ab7fb2650596980`
  - `nprocs = 64`
  - `scale_to_meters = 0.001`
  - `ncc_couples = 10`
  - `walltime = 120:00:00`
  - convergence checks enabled with:
    - `check_interval = 100`
    - `min_iterations = 500`
    - QoI `rtol = 1.0e-4`
    - QoI window `100`
    - residual targets `p_rgh = 1.0e-6`, `U = 1.0e-5`, `h = 1.0e-5`
- Water cases use `fluid = water`.
- Salt cases split by `fluid = hitec_salt_jin` and `fluid = hitec_salt_kirst`.
- Salt readable cases are all `laminar`.
- Water readable cases include both `laminar` and `kOmegaSSTLM`.

## Accessibility classification at snapshot time

### Full extractable

- All 8 salt cases
- `val_water_test_1_coarse_mesh_laminar`
- `val_water_test_2_coarse_mesh_laminar`

These cases had readable:

- `case_config.yaml`
- `system/controlDict`
- `logs/log.foamRun`
- `postProcessing/`
- `constant/polyMesh/boundary`

### Partial extractable

- `val_water_test_4_coarse_mesh_laminar`

This case had readable `case_config.yaml`, `system/controlDict`,
`logs/log.foamRun`, and `postProcessing/`, but not
`constant/polyMesh/boundary` in this snapshot.

### Partial metadata only

- `val_water_test_2_coarse_mesh_kOmegaSSTLM`
- `val_water_test_3_coarse_mesh_kOmegaSSTLM`

These cases had readable `case_config.yaml`, `system/controlDict`, and
`constant/polyMesh/boundary`, but not `logs/log.foamRun` or
`postProcessing/`.

### Blocked

- `val_water_test_1_coarse_mesh_kOmegaSSTLM`
- `val_water_test_3_coarse_mesh_laminar`
- `val_water_test_4_coarse_mesh_kOmegaSSTLM`

These remained unreadable enough that even `case_config.yaml` could not be
depended on during this pass.

## Operating-point map

### Salt viscosity screen

- `salt_test_1_jin` / `salt_test_1_kirst`: heater `232.3 W`, cooler
  `55.58 W`, `T_init = 440.0 K`
- `salt_test_2_jin` / `salt_test_2_kirst`: heater `265.7 W`, cooler
  `56.34 W`, `T_init = 447.0 K`
- `salt_test_3_jin` / `salt_test_3_kirst`: heater `297.5 W`, cooler
  `60.55 W`, `T_init = 459.0 K`
- `salt_test_4_jin` / `salt_test_4_kirst`: heater `337.6 W`, cooler
  `65.98 W`, `T_init = 475.0 K`

### Water validation/model sweep

- `water_test_1` laminar: heater `58.8 W`, cooler `26.86 W`,
  `T_init = 314.515625 K`
- `water_test_2` laminar: heater `77.6 W`, cooler `35.63 W`,
  `T_init = 320.26375 K`
- `water_test_2` `kOmegaSSTLM`: same operating point as laminar variant
- `water_test_3` `kOmegaSSTLM`: heater `93.0 W`, cooler `43.02 W`,
  `T_init = 324.390625 K`
- `water_test_4` laminar: heater `129.0 W`, cooler `58.06 W`,
  `T_init = 334.15375 K`

## Inferred interpretation

- This is no longer a single-case workspace problem. There is enough source
  material here to support a real multi-case comparison campaign.
- The salt batch is the cleanest first target because it is internally paired,
  fully readable in this snapshot, and already organized as a controlled
  property-model screen.
- The water batch is valuable for 1D-to-3D comparison because it sweeps both
  operating point and turbulence model, but the current permission state still
  makes it risky to promise a complete extraction pass immediately.

## Contradictions and risks

- Source readability is not stable while `chmod` is still running. Any blocked
  classification may disappear on a later pass without the underlying case
  changing.
- Partial water visibility means a naive automated bulk intake would mix fully
  extractable cases with cases that still lack solver outputs or mesh boundary
  artifacts.
- Registering every case immediately would overstate readiness; a staged,
  class-aware intake is safer.

## Recommended next actions

1. Freeze this inventory as the dated baseline.
2. Re-run the same audit after permissions settle.
3. Register and stage the 8 salt cases plus the 2 fully readable water
   laminar cases first.
4. Hold partial and blocked water cases in inventory-only status until the
   second pass confirms stable readability.
5. After local staging, build per-case extraction products and then assemble
   cross-case comparison tables for salt-property and turbulence-model studies.
