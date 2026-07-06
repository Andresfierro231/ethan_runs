# Ethan Boundary Modeling Report

Generated: `2026-06-16`

## Purpose

Document, from the readable local 3D case artifacts, how `ethan_runs` models
the heater, cooler, test section, insulation, and closely related wall-loss
surrogates. This revision is written for numerical-analysis use, so it focuses
on the governing `0/T` implementation, cross-case consistency, layer
coefficients, and reconciliation against the lighter metadata views.

## Scope

- This report is about the readable 3D OpenFOAM case artifacts in this
  workspace, especially `case_config.yaml` and `0/T`.
- It does not treat `two_d_*` or `one_d_stage*` comparison-contract columns as
  direct evidence of the native 3D implementation; the metadata package
  explicitly warns against that:
  [reports/2026-06-04_ethan_case_metadata_index/README.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/README.md:4).
- No new OpenFOAM jobs were launched. All claims here come from static local
  file reads and cross-case comparison.
- The report is strongest for:
  - native Salt 2 continuation:
    [case_config.yaml](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml:1),
    [0/T](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:36)
  - staged salt viscosity-screening cases:
    [salt test 2 Jin 0/T](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/0/T:36)
  - readable water laminar validation cases:
    [water test 2 0/T](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:36)

## Executive Answer

The readable Ethan cases are not conjugate-heat-transfer models with resolved
heater solids, cooler jacket flow, or insulation volumes. They solve the loop
fluid and represent external hardware through wall boundary conditions in
`0/T`.

- Standard external walls use `rcExternalTemperature` with explicit layered
  thermal stacks, ambient `Ta`, surrounding temperature `Tsur`, and
  emissivity:
  [native salt junction example](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:37),
  [native salt heater example](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577).
- The heater is modeled as three powered `rcExternalTemperature` wall patches
  on the lower leg, each with explicit `Q` and `powerLayer 1`.
- The cooler branch is modeled as fixed-`Q` `externalTemperature` sink patches
  on the cooler and the two adjacent reducers, not as a resolved coolant-side
  domain:
  [native salt cooler block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:919),
  [water test 2 cooler block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:919).
- The test section is not modeled uniformly across case families. Readable
  salt-family cases power it with `Q = 37 W`; readable water laminar cases use
  the same patch as a passive `rcExternalTemperature` wall:
  [native salt test section](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:1147),
  [water test 2 test section](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:1147).
- Insulation is represented by explicit outer `thicknessLayers` in
  `rcExternalTemperature`, not by a separately meshed solid region. The
  readable cases use about `1.65 in`, `1.40 in`, or `0.40 in` outer
  insulation, depending on family:
  [metadata index row set](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv:2).

## Case Setup Map

### What the readable 3D case actually contains

| Setup layer | Where it lives | What it controls | Safe description |
| --- | --- | --- | --- |
| Operating-point and nominal setup metadata | [case_config.yaml](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/case_config.yaml:1) | fluid branch, turbulence model, heater/cooler/test-section nominal inputs, mesh/run-control metadata | This is the human-readable case recipe, but not the final authoritative thermal BC implementation. |
| Governing thermal boundary implementation | [0/T](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/0/T:36) | actual heater, cooler, insulation, ambient, emissivity, and test-section wall numerics | This is the authoritative setup file for how Ethan is thermally modeled in the readable 3D cases. |
| Runtime / write behavior | [system/controlDict](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/system/controlDict:1) | solver application, latest-time restart, adaptive timestep, write interval, linked runtime functions | This controls how the case runs, not the physical hardware abstraction itself. |
| Fluid and transport models | [constant/physicalProperties](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/constant/physicalProperties), [constant/momentumTransport](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/constant/momentumTransport), [constant/thermophysicalTransport](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/constant/thermophysicalTransport) | fluid-property law, momentum/thermal transport closures | Jin/Kirst differences primarily live here, not in different heater/cooler BC topology. |
| Geometry and mesh | [constant/geometry](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/constant/geometry), [constant/polyMesh](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/constant/polyMesh) | STL-based loop geometry, patch names, mesh connectivity, NCC interfaces | The readable Ethan case is a single-fluid-region mesh with named wall patches; external hardware is imposed through those patch BCs. |

### What is physically resolved versus surrogate

| Physical subsystem | Resolved volume in readable case? | How it appears instead | Main evidence |
| --- | --- | --- | --- |
| Loop fluid | yes | fluid solved directly in the OpenFOAM case | [system/controlDict](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/system/controlDict:16), [case_config.yaml](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/case_config.yaml:1) |
| Heater solids | no | three powered lower-leg `rcExternalTemperature` patches | [0/T heater block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577) |
| Cooler jacket / secondary fluid | no | three fixed-sink `externalTemperature` cooling-branch patches | [0/T cooler block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:919) |
| Insulation | no | explicit outer wall layers inside `rcExternalTemperature` stacks | [0/T junction block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:37) |
| Test-section hardware | partly surrogate | dedicated left-leg patch, powered in readable salt and passive in readable water | [salt test section](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:1147), [water test section](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:1147) |
| Radiation / ambient exchange | not a separate radiation domain | embedded in wall BC coefficients through `Tsur` and `emissivity` | [0/T heater block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577) |

### One-pass description of the loop setup

The readable Ethan 3D cases are single-fluid OpenFOAM loop models with shared
mesh and runtime scaffolding, variant fluid-property branches, and patch-based
thermal surrogates for all external hardware. Heater power is injected on the
lower leg, cooling is removed on the upper cooling branch, the test section
lives on the left leg, and the remaining transport walls lose heat through
layered ambient-coupled wall models rather than through resolved external
solids or a resolved jacket domain.

### Thermal-role map around the loop

| Loop span | Dominant thermal role in readable setup | Representative patch names | Evidence |
| --- | --- | --- | --- |
| Lower leg | imposed heater plus ambient loss | `pipeleg_lower_04_straight`, `pipeleg_lower_05_straight`, `pipeleg_lower_06_straight` | [heater blocks](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577), [thermal role map](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/case_analysis_profiles.py:396) |
| Right leg | transport / parasitic loss wall family | right-leg transport patches in `SALT2_MAJOR_SPANS` | [thermal role map](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/case_analysis_profiles.py:430), [native salt junction block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:37) |
| Upper leg | imposed cooling sink plus adjacent transport walls | `pipeleg_upper_04_reducer`, `pipeleg_upper_05_cooler`, `pipeleg_upper_06_reducer` | [cooler blocks](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:919), [thermal role map](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/case_analysis_profiles.py:396) |
| Left leg | transport walls plus dedicated test-section patch | `pipeleg_left_04_test_section` and neighboring left-leg walls | [test-section block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:1147), [left-leg wall block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:1128) |

## How To Read An Ethan Case

If the question is "how is this Ethan case set up?", the most reliable file
read order is:

1. `case_config.yaml`
   - identify the fluid branch, turbulence model, operating point, and nominal
     BC metadata
2. `system/controlDict`
   - confirm the solver application, restart behavior, write cadence, and
     runtime function includes
3. `0/T`
   - determine the actual heater, cooler, test-section, ambient, emissivity,
     and insulation implementation
4. `constant/physicalProperties`, `constant/momentumTransport`, and
   `constant/thermophysicalTransport`
   - identify the actual fluid-property and transport law family
5. `constant/polyMesh/boundary` plus the geometry tree
   - verify patch names and the single-fluid-region mesh structure

That order avoids the main failure mode in this workspace: assuming nominal
metadata fields map one-to-one onto the final thermal BC numerics.

## Evidence Base

### Primary files

- Metadata glossary and case-index explanation:
  [reports/2026-06-04_ethan_case_metadata_index/README.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/README.md:1)
- Metadata rows:
  [reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv:2)
- Common campaign setup summary:
  [operational_notes/2026-06-01_modern_runs_source_inventory.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/2026-06-01_modern_runs_source_inventory.md:10)
- Thermal-role grouping used elsewhere in the workspace:
  [tools/case_analysis_profiles.py](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/case_analysis_profiles.py:396)

### Governing-file rule

For numerical interpretation, `0/T` is the governing implementation. The
metadata package is still useful, but it stores some nominal setup knobs that
do not appear one-to-one in the final OpenFOAM boundary file. The major
examples are the emissivity mismatch and cooler-`h` to fixed-`Q` transition,
documented later in this report.

## Case Families And Provenance Boundary

The readable cases relevant here fall into three practical groups.

| Group | Representative source IDs | Fluid / model | Primary files used here | Notes |
| --- | --- | --- | --- | --- |
| Native Salt 2 continuation | `val_salt_test_2_coarse_mesh_laminar` continuation tree | `hitec_salt`, laminar | [case_config.yaml](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml:1), [0/T](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:36) | Deliberate continuation-aware exception in the metadata package. |
| Staged salt viscosity screen | `viscosity_screening_salt_test_[1-4]_{jin,kirst}_coarse_mesh` | `hitec_salt_jin` or `hitec_salt_kirst`, laminar | [salt test 2 Jin case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/case_config.yaml:1), [salt test 2 Jin 0/T](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/0/T:36) | At the boundary-condition level, Jin/Kirst partners appear identical for the same test number in the readable `0/T` files. |
| Readable water laminar validation | `val_water_test_[1-4]_coarse_mesh_laminar` | `water`, laminar | [water test 2 case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/case_config.yaml:1), [water test 2 0/T](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:36) | Water `kOmegaSSTLM` exists in campaign metadata, but this report only uses the readable laminar `0/T` cases. |

## Shared Numerical Setup

The readable cases share a common numerical scaffold, which matters when
comparing boundary-condition behavior across families.

- `mesh_group_id = 7ab7fb2650596980`
- `nprocs = 64`
- `scale_to_meters = 0.001`
- `ncc_couples = 10`
- `walltime = 120:00:00`
- convergence monitor enabled with:
  - `check_interval = 100`
  - `min_iterations = 500`
  - QoI `rtol = 1.0e-4`
  - QoI `window = 100`
  - residual targets: `p_rgh = 1.0e-6`, `U = 1.0e-5`, `h = 1.0e-5`

Sources:
[operational_notes/2026-06-01_modern_runs_source_inventory.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/operational_notes/2026-06-01_modern_runs_source_inventory.md:12),
[native salt case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml:20),
[water test 2 case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/case_config.yaml:20).

Interpretation:

- The boundary-condition differences discussed below are not accompanied by a
  wholesale change in mesh scale, rank count, or NCC topology.
- The readable cases are therefore suitable for controlled BC-structure
  comparison.

## Boundary-Condition Taxonomy

Three boundary-condition types carry almost the entire thermal-modeling burden.

| BC type | What it does here | Typical fields present | Representative evidence |
| --- | --- | --- | --- |
| `zeroGradient` | Internal or coupling interface; not external loss hardware | none beyond the type | [native salt NCC interface](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:55) |
| `rcExternalTemperature` | Layered wall model with optional imposed power, plus ambient and radiation-like exchange | `steadyWall`, optional `Q`, optional `powerLayer`, `h`, `Ta`, `Tsur`, `emissivity`, `internalRadius`, `thicknessLayers`, `kappaLayerCoeffs`, `rhoLayerCoeffs`, `CpLayerCoeffs` | [native salt junction](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:37), [native salt heater](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577) |
| `externalTemperature` | Lumped external sink without layered wall stack; used for fixed-`Q` cooling branch and convective stub fins | either `Q` or `h`/`Ta`, but not the layered `rcExternalTemperature` fields | [native salt stub fin](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:196), [water test 2 cooler](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:935) |

Two practical consequences follow directly from this taxonomy.

- The cases are not using a resolved multi-region solid or coolant jacket in
  the readable setup. The heat-transfer hardware appears only as BC surrogates
  on a single fluid-region temperature field.
- `first-order segment` and `stub fin` comments inside `0/T` strongly suggest
  upstream reduced-order calibration or segmentation logic. That is an
  inference from the file comments, not a direct proof of the preprocessing
  script.

## Metadata-To-Implementation Reconciliation

`case_config.yaml` and the June 4 metadata index are useful, but serious
numerical work should reconcile them against `0/T`.

| Quantity | Metadata / `case_config.yaml` | Governing `0/T` behavior | Conclusion |
| --- | --- | --- | --- |
| Heater total power | Stored as a case-level `Q` equal to operating-point `heater_power_W`, e.g. `265.7 W` for native Salt 2 and `77.6 W` for Water 2: [salt case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml:8), [water case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/case_config.yaml:8) | Split evenly across three lower-leg patches, each with `Q = heater_power_W / 3`: [native salt heater block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577), [water test 2 heater block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:577) | Direct match after repartition. |
| Heater `h` | Nominal `8.761 W/m2K` in representative readable cases: [salt case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml:10), [water case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/case_config.yaml:10) | Patch-specific values around `3.47` to `4.45 W/m2K` across readable salt and water heater patches | Not a one-to-one transfer; `0/T` uses calibrated patch values. |
| Heater `Ta` | `300 K` for salt, `298 K` for water in metadata | Actual heater-patch `Ta` values are near but not equal: about `299.11` to `299.97 K` for readable salt and `296.80` to `296.94 K` for readable water | Treated as case-built values in `0/T`, not literal metadata copies. |
| Emissivity | `0.25` in readable `case_config` metadata: [salt case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml:11) | `0/T` `rcExternalTemperature` patches use `emissivity 0.95`: [native salt heater block](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:592), [water test 2 test section](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:1157) | This is a real mismatch; use `0/T` as governing. |
| Cooler `h` | Present in metadata, e.g. `28.58 W/m2K` native Salt 2 and `105.27 W/m2K` Water 2: [salt case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml:13), [water case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/case_config.yaml:13) | Cooler patch in `0/T` is fixed negative `Q` with no layered wall model and no local `h`: [native salt cooler](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:935), [water test 2 cooler](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:935) | The preprocessing path from nominal cooler `h` to final fixed-`Q` sink is not visible in the readable artifacts. |
| Test-section `h` | Nominal `5.964 W/m2K` in readable metadata | Actual test-section `h` is family- and test-dependent: about `7.45` to `7.70 W/m2K` in readable salt and `4.45` to `5.41 W/m2K` in readable water | Again, `0/T` is the governing implementation. |

## Common Wall-Layer Materials

The readable files repeatedly reuse a small set of layer-coefficient families.
This is numerically important because the heater, test section, and passive
loss walls are all built by arranging these same materials in different orders
and thicknesses.

| Functional layer | Representative location | Thickness role | `kappaLayerCoeffs` | `rhoLayerCoeffs` | `CpLayerCoeffs` | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Standard metal wall | pipe straights, bends, many junctions | inner structural wall | `(9.248 0.01571 0 0 0 0 0 0)` | `(8084.2 -0.42086 -3.8942e-05 0 0 0 0 0)` | `(458.98 0.1328 0 0 0 0 0 0)` | [native salt junction](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:37) |
| Heater layer | powered lower-leg heater patches | middle powered layer | `(50 0 0 0 0 0 0 0)` | `(1200 0 0 0 0 0 0 0)` | `(1000 0 0 0 0 0 0 0)` | [native salt heater](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577) |
| Salt-family insulation | outer loss layer in readable salt cases | outer insulation | `(0.036056549855 -6.2436910698e-05 1.9275102287e-07 0 0 0 0 0)` | `(128.0 0 0 0 0 0 0 0)` | `(1000 0 0 0 0 0 0 0)` | [native salt heater](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577) |
| Water-family insulation | outer loss layer in readable water laminar cases | outer insulation | `(0.06407 -0.0001945 3.917e-07 0 0 0 0 0)` | `(64.0 0 0 0 0 0 0 0)` | `(1000 0 0 0 0 0 0 0)` | [water test 2 left-leg wall](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:1128) |
| Test-section liner / local inner wall | left-leg test section and neighboring walls | inner left-leg/test-section layer | `(1.4 0 0 0 0 0 0 0)` | `(2214.39 0 0 0 0 0 0 0)` | `(740 0 0 0 0 0 0 0)` | [native salt test section](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:1147), [water test 2 test section](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:1147) |

Interpretation:

- The wall models are not arbitrary patch-by-patch parameter dumps. They are
  structured combinations of a few material families.
- Standard transport regions, heater regions, and left-leg/test-section
  regions share material building blocks but arrange them differently.

## Heater Modeling

### Exact implementation

The heater is implemented on three lower-leg wall patches:

- `pipeleg_lower_04_straight`
- `pipeleg_lower_05_straight`
- `pipeleg_lower_06_straight`

Each is an `rcExternalTemperature` patch with:

- positive imposed `Q`
- `powerLayer 1`
- ambient `Ta`
- surrounding `Tsur`
- `emissivity`
- a three-layer wall stack:
  `metal wall + powered heater layer + outer insulation`

Representative native Salt 2 block:
[0/T:577](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577)

### Cross-case heater structure

| Case family | Heater total `Q` | Per-patch `Q` | `powerLayer` | Heater-patch `h` range in readable cases | Heater stack thicknesses |
| --- | --- | --- | --- | --- | --- |
| Native Salt 2 continuation | `265.7 W` | `88.56666666666666 W` | `1` | `3.677` to `3.850 W/m2K` | `0.001651 + 0.003175 + 0.04191 m` |
| Staged salt test 1 | `232.3 W` | `77.43333333333334 W` | `1` | `3.870` to `4.033 W/m2K` | `0.001651 + 0.003175 + 0.03556 m` |
| Staged salt test 2 | `265.7 W` | `88.56666666666666 W` | `1` | `3.893` to `4.075 W/m2K` | `0.001651 + 0.003175 + 0.03556 m` |
| Staged salt test 3 | `297.5 W` | `99.16666666666667 W` | `1` | `3.974` to `4.157 W/m2K` | `0.001651 + 0.003175 + 0.03556 m` |
| Staged salt test 4 | `337.6 W` | `112.53333333333333 W` | `1` | `4.086` to `4.268 W/m2K` | `0.001651 + 0.003175 + 0.03556 m` |
| Water laminar tests 1-4 | `58.8` to `129.0 W` | `19.6` to `43.0 W` | `1` | `3.470` to `4.448 W/m2K` | `0.001651 + 0.003175 + 0.01016 m` |

### Derived checks

- In every readable representative case inspected, the three heater-patch
  powers sum exactly to the case `heater_power_W`.
- The heater is not a pure Neumann flux with no losses. It remains embedded in
  a wall model that can still exchange heat outward through the external-loss
  terms.
- The case-level heater `h = 8.761 W/m2K` in metadata does not match the
  implemented patchwise heater `h`. The governing numerics therefore live in
  the patch-calibrated `0/T` values.

### Numerical-analysis implication

If a later reduced-order model or inverse analysis treats the heater as a
simple prescribed total power with adiabatic exterior, it will not reproduce
the actual 3D boundary treatment. The 3D implementation is a combined
power-plus-loss wall surrogate.

## Cooler And Cooling Jacket Modeling

### Exact implementation

The cooling branch in readable `0/T` files consists of three
`externalTemperature` fixed-sink patches:

- `pipeleg_upper_04_reducer`
- `pipeleg_upper_05_cooler`
- `pipeleg_upper_06_reducer`

Representative Water 2 block:
[0/T:919](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:919)

Representative Native Salt 2 block:
[0/T:919](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:919)

The main cooler-patch comments explicitly decompose the fixed removal into an
air-side part and a jacket-to-ambient part:

- Native Salt 2:
  `Q_loss = 104.07 W (air-side 67.33 + jacket-to-ambient 36.74)` at
  [0/T:935](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:935)
- Water test 2:
  `Q_loss = 38.97 W (air-side 36.89 + jacket-to-ambient 2.08)` at
  [0/T:935](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:935)

### Cross-case cooler behavior

| Case family | Nominal `cooling_power_W` from metadata | Main cooler fixed `Q` | Reducer fixed `Q` each | Total cooling-branch sink | Branch / nominal ratio |
| --- | --- | --- | --- | --- | --- |
| Native Salt 2 continuation | `56.34 W` | `104.07353581998868 W` | `16.13860204279952 W` | `136.35073990558772 W` | `2.420` |
| Staged salt test 1 | `55.58 W` | `103.16215407994024 W` | `16.22051188331554 W` | `135.60317784657132 W` | `2.440` |
| Staged salt test 2 | `56.34 W` | `104.07353581998868 W` | `16.13860204279952 W` | `136.35073990558772 W` | `2.420` |
| Staged salt test 3 | `60.55 W` | `114.57817713779176 W` | `18.095730767834933 W` | `150.76963867346162 W` | `2.490` |
| Staged salt test 4 | `65.98 W` | `128.1485764924187 W` | `20.539119272541168 W` | `169.22681503750102 W` | `2.565` |
| Water test 1 | `26.86 W` | `29.103456575197743 W` | `0.6452509647901099 W` | `30.393958504777963 W` | `1.132` |
| Water test 2 | `35.63 W` | `38.96629156499222 W` | `0.9301009744684897 W` | `40.8264935139292 W` | `1.146` |
| Water test 3 | `43.02 W` | `47.16193197434059 W` | `1.1306360911783977 W` | `49.42320415669739 W` | `1.149` |
| Water test 4 | `58.06 W` | `64.54984858230077 W` | `1.6807716920695308 W` | `67.91139196643982 W` | `1.170` |

### Interpretation

- The cooler is not modeled as a resolved secondary fluid or jacket region.
- The readable files treat the cooling jacket as bookkeeping inside the imposed
  sink. The comment text literally includes `jacket-to-ambient` inside the
  cooler patch removal.
- The branch sink exceeds the nominal `cooling_power_W` because the branch also
  includes reducer losses and the extra jacket-to-ambient removal.
- The salt-family branch sink is much larger, relative to nominal cooler duty,
  than in the readable water family.

### Numerical-analysis implication

The fixed-`Q` cooler patches do not depend on local wall-to-ambient
temperature difference in the same way a live convective jacket model would.
That matters for:

- sensitivity analysis
- transient interpretation
- reduced-order closure fitting
- any attempt to back out a physical cooler-side `hA` from the 3D results

The readable setup is better interpreted as an imposed thermal sink model than
as a directly predictive cooler-jacket submodel.

## Test Section Modeling

### Salt-family implementation

Readable salt-family cases use a powered test-section patch:

- patch name: `pipeleg_left_04_test_section`
- type: `rcExternalTemperature`
- `Q = 37.0 W`
- `powerLayer = 0`
- single-layer stack:
  `thicknessLayers (0.002199999999999999)`

Representative native Salt 2 block:
[0/T:1147](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:1147)

### Water-family readable implementation

Readable water laminar cases use the same named patch as a passive wall:

- type: `rcExternalTemperature`
- no `Q`
- no `powerLayer`
- same single `0.0022 m` layer

Representative Water 2 block:
[0/T:1147](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:1147)

### Cross-case summary

| Family | Test-section mode | `Q` | `powerLayer` | Readable `h` range |
| --- | --- | --- | --- | --- |
| Native Salt 2 continuation | powered | `37.0 W` | `0` | `7.482 W/m2K` |
| Staged salt tests 1-4 | powered | `37.0 W` | `0` | `7.449` to `7.704 W/m2K` |
| Water laminar tests 1-4 | passive | none | none | `4.449` to `5.412 W/m2K` |

### Neighboring left-leg structure

The unpowered walls adjacent to the test section use a three-layer left-leg
stack:

- inner `0.0022 m` test-section-like layer
- `0.006096001 m` metal layer
- outer insulation layer

Examples:
[native salt left-leg wall](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:1128),
[water test 2 left-leg wall](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/water/val_water_test_2_coarse_mesh_laminar/0/T:1128)

This means the test-section region is not just one isolated special patch. It
is embedded in a local left-leg wall family with different inner-wall material
and geometry from the standard loop sections.

### Numerical-analysis implication

The readable salt and water cases should not be forced into one shared
test-section boundary model without an explicit abstraction step. Salt-family
cases have an extra imposed energy source there; water-family readable cases do
not.

## Insulation Modeling

### General rule

Insulation is represented as an outer layer inside `rcExternalTemperature`.
There is no readable evidence of a separately resolved insulation volume mesh.

### Region-dependent wall stacks

| Region type | Representative stack | Interpretation |
| --- | --- | --- |
| Standard pipe straights / bends | `0.001651 + outer insulation` | metal wall plus insulation |
| Junctions and many fittings | `0.006096001 + outer insulation` | thicker structural wall plus insulation |
| Heater walls | `0.001651 + 0.003175 + outer insulation` | metal wall + powered heater layer + insulation |
| Left-leg walls near test section | `0.0022 + 0.006096001 + outer insulation` | test-section-like inner layer + metal wall + insulation |
| Test-section patch itself | `0.0022` only | single local inner wall; powered in salt, passive in water |

Evidence:
[native salt junction](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:37),
[native salt heater](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:577),
[native salt left-leg wall](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:1128)

### Cross-family outer insulation thickness

| Family | Outer insulation thickness in `0/T` | Metadata equivalent |
| --- | --- | --- |
| Native Salt 2 continuation | `0.04191 m` | `1.65 in` |
| Staged salt viscosity-screening cases | `0.03556 m` | `1.40 in` |
| Readable water laminar cases | `0.01016 m` | `0.40 in` |

Sources:
[native Salt 2 row](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv:2),
[staged Salt 2 Jin row](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv:5),
[water 2 row](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv:12)

### Numerical-analysis implication

When comparing heat-loss behavior across families, insulation thickness is one
of the largest explicit setup changes. The salt and water cases are therefore
not simply a fluid-property swap at common external-loss geometry.

## Auxiliary External Features

This report is centered on heater, cooler, test section, and insulation, but a
serious numerical reading should also note one additional wall-loss surrogate
family.

- Several stub or cap features use `externalTemperature` with calibrated
  `h` and `Ta`, without the layered `rcExternalTemperature` structure.
- Native Salt 2 example:
  `junction_lower_left_left_stub`, with comment
  `Q_loss = 4.959 W @ T_init -> h_cal = 84.893 W/m2K`:
  [0/T:196](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T:196)

Interpretation:

- Not all external-loss hardware is represented through layered conduction.
- The readable setup mixes fixed-sink surrogates, layered loss walls, and
  calibrated pure-convection surrogates.

## Cross-Case Consistency Findings

### What is consistent

- All readable cases use the same three-patch lower-leg heater topology.
- All readable cases use the same three-patch cooling-branch topology.
- Standard pipe/junction material families are reused broadly.
- Mesh scale, processor count, NCC count, and convergence settings are shared
  across the readable modern-run families.

### What changes materially by family or operating point

- Outer insulation thickness
- actual patchwise `h`
- actual ambient `Ta`
- cooler branch fixed `Q`
- test-section power state
- fluid-property models

### Jin vs Kirst

At the boundary-condition level, readable Jin/Kirst partner cases for the same
salt test number appear identical in `0/T` for:

- heater power split
- heater patch `h`
- test-section treatment
- cooler branch fixed `Q`
- outer insulation thickness

The readable difference between those pairs is therefore primarily in the fluid
property model branch, not the boundary-condition structure:
[salt test 2 Jin case_config](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh/case_config.yaml:1)

## Contradictions And Open Questions

### Emissivity mismatch

- `case_config.yaml` stores `heater.emissivity = 0.25` in the readable cases.
- Representative `0/T` `rcExternalTemperature` patches use `emissivity 0.95`.

This is a hard contradiction between metadata and governing BC files. The safe
rule is to treat `0/T` as numerically authoritative unless a preprocessing
script can be found that explains the translation.

### Cooler nominal `h` versus fixed-`Q` implementation

- Metadata preserves a nominal cooler-side `h` and `Ta`.
- The readable `0/T` cooler branch is fixed `Q`.

The missing link is the transformation path that converted nominal cooler
inputs into final fixed sinks. Until that path is found, the correct statement
is not “the cooler uses `h = ...`” but rather “metadata stores a nominal
cooler `h`, while the governing `0/T` applies a fixed cooling-branch sink.”

### Meaning of the powered salt test section

The readable salt-family cases impose a powered `37 W` test section while the
water-family readable cases do not. What remains unresolved is whether that is

- a direct representation of a real experimental heating element,
- a calibration surrogate used only in some campaigns, or
- a family-specific closure carried over from an upstream first-order model.

The current local evidence supports the fact of the imposed power, not the
historical rationale.

### Upstream generation logic

The comments in `0/T` are highly structured, and several metadata fields do
not map directly into the final BC numerics. That strongly suggests an
upstream generation step, but this pass did not identify the script or template
that produced the readable `0/T` files.

## Bottom Line

For serious numerical analysis of `ethan_runs`, the correct model description
is:

- Heater: three lower-leg powered `rcExternalTemperature` patches with total
  case heater power split evenly, injected into `powerLayer 1`, and still
  coupled to ambient/radiation-like losses through the same wall model.
- Cooler: three fixed-`Q` `externalTemperature` sink patches on the cooling
  branch; the readable comments explicitly lump air-side and
  jacket-to-ambient removal into that imposed sink.
- Test section: powered `37 W` single-layer `rcExternalTemperature` in the
  readable salt-family cases, passive single-layer `rcExternalTemperature` in
  the readable water laminar cases.
- Insulation: explicit outer wall layers inside `rcExternalTemperature`, with
  family-dependent thickness and region-dependent wall-stack composition.
- Governing source of truth: the final `0/T` file, not the nominal
  `case_config.yaml` fields by themselves.
