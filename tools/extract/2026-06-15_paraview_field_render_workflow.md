# ParaView Field Render Workflow

Date: `2026-06-15`

This note documents the working workflow used for the reusable ParaView field
slice renderers in:

- `tools/extract/render_last_timestep_field_slices.py`
- `tools/extract/stage_latest_time_field_reconstruction.py`

The current canonical output tree is:

- `figures/figures_rendered/paraview_field_families/`

The earlier root-level `figures_rendered/` batch was left in place for
comparison and should not be treated as the canonical destination.

## What the renderer does

`render_last_timestep_field_slices.py` renders the latest reconstructed time
from registered cases to PNG, SVG, and PDF. It now supports:

- `temperature`
- `velocity`
- `velocity_x`
- `velocity_y`
- `velocity_z`
- `pressure_static`
- `pressure_dynamic`
- `pressure_total`

It also supports repeatable component-focused views:

- `upcomer`
- `downcomer`
- `cooler`
- `heater`

The component views are not hand-tuned clips. They are derived from Salt-family
case metadata plus `constant/polyMesh` patch geometry, so the same selector is
reusable across the active Salt-family cases.

## Default rendering contract

- Array association defaults to `cells`, not `points`.
- This is intentional for non-conforming coupling visibility.
- For this render family, the success criterion is the written artifacts plus
  the status JSON, not the raw `pvbatch` exit code.

ParaView currently writes the requested outputs and then often segfaults during
MPI shutdown. This was observed consistently in the current batch and is an
accepted caveat for this workflow.

## Standard environment

Run the ParaView rendering step on a compute node, not a login node.

The working ParaView environment for the current batch was:

```bash
module load gcc/11.2.0 paraview_osmesa/5.13.3
unset TACC_PARAVIEW_BIN
```

The render command then uses:

```bash
mpiexec -n 1 "$TACC_PARAVIEW_OSMESA_BIN/pvbatch" ...
```

## Basic render command

Example: one field, one component, one case.

```bash
module load gcc/11.2.0 paraview_osmesa/5.13.3
unset TACC_PARAVIEW_BIN

mpiexec -n 1 "$TACC_PARAVIEW_OSMESA_BIN/pvbatch" \
  tools/extract/render_last_timestep_field_slices.py \
  --source-id val_salt_test_2_coarse_mesh_laminar \
  --field temperature \
  --component upcomer \
  --output-root figures/figures_rendered/paraview_field_families
```

Useful arguments:

- `--source-id`: repeat to select multiple registered cases
- `--field`: required
- `--component`: `all`, `upcomer`, `downcomer`, `cooler`, or `heater`
- `--output-root`: default is `figures`, but the canonical durable tree for
  this work is `figures/figures_rendered/paraview_field_families`
- `--status-path`: optional override for the machine-readable status JSON
- `--array-association`: defaults to `cells`

## Component-batch command used for the canonical tree

The component-view family under `figures/figures_rendered/` was generated with
the same renderer and the following pattern:

```bash
module load gcc/11.2.0 paraview_osmesa/5.13.3
unset TACC_PARAVIEW_BIN

for component in upcomer downcomer cooler heater; do
  for field in temperature velocity velocity_x velocity_y velocity_z; do
    mpiexec -n 1 "$TACC_PARAVIEW_OSMESA_BIN/pvbatch" \
      tools/extract/render_last_timestep_field_slices.py \
      --source-id val_salt_test_2_coarse_mesh_laminar \
      --source-id viscosity_screening_salt_test_1_kirst_coarse_mesh \
      --source-id viscosity_screening_salt_test_3_jin_coarse_mesh \
      --source-id viscosity_screening_salt_test_4_jin_coarse_mesh \
      --field "$field" \
      --component "$component" \
      --output-root figures/figures_rendered/paraview_field_families || true
  done
done
```

The trailing `|| true` is deliberate. It lets the loop continue after the
known post-write ParaView shutdown segfault.

## Output layout

For component-scoped families, every field now lives under:

- `figures/figures_rendered/paraview_field_families/<component>/<field>/png/`
- `figures/figures_rendered/paraview_field_families/<component>/<field>/svg/`
- `figures/figures_rendered/paraview_field_families/<component>/<field>/pdf/`

Canonical field directory names for the current non-pressure batch are:

- `temperature`
- `velocity`
- `x_vel`
- `y_vel`
- `z_vel`

Examples:

- `figures/figures_rendered/paraview_field_families/upcomer/temperature/svg/`
- `figures/figures_rendered/paraview_field_families/upcomer/velocity/svg/`
- `figures/figures_rendered/paraview_field_families/upcomer/y_vel/svg/`

Status files follow this pattern:

- `last_timestep_<field>_<component>_slice_status.json`

Example:

- `figures/figures_rendered/paraview_field_families/upcomer/temperature/last_timestep_temperature_upcomer_slice_status.json`
- `figures/figures_rendered/paraview_field_families/heater/z_vel/last_timestep_velocity_z_heater_slice_status.json`

## Pressure staging workflow

Pressure rendering required an extra staging fix because the reconstructed
render-input mirrors initially only contained `T` and `U`.

The current helper script:

- stages a local render mirror under `staging/render_inputs/<source_id>/reconstructed_case`
- materializes writable local copies of `constant/` and `system/`
- leaves `--new-times-only` off by default so new fields can be backfilled into
  an existing latest-time mirror

That behavior matters because:

- `reconstructPar -newTimes` will not backfill a new field into an already
  existing latest-time directory
- OpenFOAM 13 needs writable local `constant/` and `system/` content for this
  reconstruction path

The working OpenFOAM bootstrap for pressure reconstruction was:

```bash
source jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh
export LD_LIBRARY_PATH="/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data:${LD_LIBRARY_PATH:-}"
unset FOAM_SIGFPE
```

Example backfill command:

```bash
source jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh
export LD_LIBRARY_PATH="/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data:${LD_LIBRARY_PATH:-}"
unset FOAM_SIGFPE

python3.11 tools/extract/stage_latest_time_field_reconstruction.py \
  --source-id val_salt_test_2_coarse_mesh_laminar \
  --field p \
  --status-path staging/render_inputs/2026-06-15_paraview_pressure_static_backfill_status.json
```

Important observations:

- Reconstructing `p` under the incompatible OpenFOAM 12 path failed.
- The OpenFOAM 13 bootstrap plus `libRCWallBC.so` on `LD_LIBRARY_PATH` worked.
- The helper now supports safe field backfill into an existing latest-time
  mirror.

## Pressure caveat for future use

The script still supports:

- `pressure_static`
- `pressure_dynamic`
- `pressure_total`

Current formulas:

- `pressure_static = p`
- `pressure_dynamic = 0.5 * rho * |U|^2`
- `pressure_total = p + 0.5 * rho * |U|^2`

For the current user-facing durable figure batch, dynamic and total pressure
were intentionally not generated. The derived dynamic-pressure path did not
look good in the fixed-pressure context, so the durable component-view batch
skipped pressure entirely.

If pressure figures are revisited, treat `pressure_static` as the safer first
path and validate the interpretation before publishing any derived pressure
family.

## Validation pattern

Do not judge this workflow by the raw `pvbatch` exit code alone.

Validate by checking:

1. The expected PNG/SVG/PDF files exist.
2. The matching status JSON exists.
3. The status JSON reports:
   - `case_count` as expected
   - `rendered_count` as expected
   - `failed_count: 0`
4. For cell-association-sensitive views, confirm:
   - `requested_array_association: "cells"`
   - per-case `resolved_array_association: "CELLS"`

Representative verified status artifacts from the canonical tree:

- `figures/figures_rendered/paraview_field_families/upcomer/temperature/last_timestep_temperature_upcomer_slice_status.json`
- `figures/figures_rendered/paraview_field_families/downcomer/velocity/last_timestep_velocity_downcomer_slice_status.json`
- `figures/figures_rendered/paraview_field_families/cooler/x_vel/last_timestep_velocity_x_cooler_slice_status.json`
- `figures/figures_rendered/paraview_field_families/heater/z_vel/last_timestep_velocity_z_heater_slice_status.json`

## What specifically had to be fixed

In `render_last_timestep_field_slices.py`:

- cell association is now the default
- velocity component fields were added
- pressure fields were added
- the `velocity` calculator path was kept on cell data
- metadata-driven component clipping was added for Salt-family cases
- output routing now supports component and field-family subtrees cleanly

In `stage_latest_time_field_reconstruction.py`:

- `constant/` and `system/` are copied locally instead of only symlinked
- new-field backfill is now allowed by default
- `--new-times-only` became an explicit opt-in instead of the default behavior

## Current verified result set

The canonical component-view batch currently exists under:

- `figures/figures_rendered/paraview_field_families/upcomer/`
- `figures/figures_rendered/paraview_field_families/downcomer/`
- `figures/figures_rendered/paraview_field_families/cooler/`
- `figures/figures_rendered/paraview_field_families/heater/`

Within each component directory, the current fields are:

- `temperature/`
- `velocity/`
- `x_vel/`
- `y_vel/`
- `z_vel/`

Verified result summary for the component tree:

- 20 component/field status files checked
- each reported `case_count: 4`
- each reported `rendered_count: 4`
- each reported `failed_count: 0`

## Representative movie workflow

The representative movie path is implemented in:

- `tools/extract/render_representative_field_movies.py`

The current durable output root is:

- `figures/figures_rendered/paraview_movies/`

Representative cases:

- `viscosity_screening_salt_test_1_jin_coarse_mesh`
- `val_salt_test_2_coarse_mesh_laminar`
- `viscosity_screening_salt_test_3_jin_coarse_mesh`
- `viscosity_screening_salt_test_4_jin_coarse_mesh`
- `val_water_test_1_coarse_mesh_laminar`
- `val_water_test_2_coarse_mesh_laminar`
- `val_water_test_3_coarse_mesh_laminar`
- `val_water_test_4_coarse_mesh_laminar`

Supported movie fields:

- `temperature`
- `velocity_y`

Each movie is a fixed 5-panel layout:

- full-loop overview
- `upcomer`
- `downcomer`
- `heater`
- `cooler`

Per-movie rendering contract:

- one fixed color range per case/field movie
- `velocity_y` uses symmetric bounds about zero
- panel titles include `source_id`, field, and branch name
- time stamps are shown in each panel
- canonical PNG frame sequences are always retained
- the renderer now also supports `--frames-only` to skip packaged video output
- explicit frame resolution is controlled with `--image-width` and
  `--image-height`

Durable per-movie files:

- `figures/figures_rendered/paraview_movies/<source_id>/<field>/frames/`
- `figures/figures_rendered/paraview_movies/<source_id>/<field>/<source_id>_<field>.ogv`
- `figures/figures_rendered/paraview_movies/<source_id>/<field>/status.json`
- `figures/figures_rendered/paraview_movies/<source_id>/<field>/run_status.json`

### All-times frame refresh

On `2026-06-16`, the movie path was extended to support a longer-history
refresh in high-resolution PNG-frame mode.

Key changes:

- `stage_latest_time_field_reconstruction.py` now resolves the richest
  available source root before reconstruction staging. If a matching
  continuation-stage case under `jadyn_runs/**/case_stage/` has more retained
  times than the registered `source_root`, that richer continuation tree is
  preferred for reconstruction staging.
- `render_representative_field_movies.py` now supports:
  - `--frames-only`
  - `--image-width`
  - `--image-height`
- In frames-only mode, the renderer writes explicit PNG screenshots for the
  requested frame-time list instead of relying on ParaView `SaveAnimation` for
  the frame sequence.
- The frame-time list now follows the staged/source numeric times chosen for
  the case, which is necessary when ParaView's scene timestep list drops
  `t=0`.

This matters most for representative Salt 2:

- the registered source root only exposed the early retained window through
  `1724`
- the continuation-stage case under
  `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation`
  exposes the longer retained window through `8602`
- the June 16 all-times refresh therefore stages Salt 2 from the continuation
  tree instead of the shorter imported root

Batch-wrapper caveat discovered during this refresh:

- the OpenFOAM 13 bootstrap script must be sourced outside `set -euo pipefail`
  because its bashrc path is not safe under strict pipefail mode
- after reconstruction, the wrapper must `module purge` and then load
  `gcc/11.2.0`, `impi/19.0.9`, and `paraview_osmesa/5.13.3` before invoking
  `pvbatch`

Tracked launch artifacts for the June 16 refresh:

- import manifest:
  `imports/2026-06-16_paraview_movie_all_times_refresh.json`
- stage status:
  `staging/render_inputs/2026-06-16_paraview_movie_all_times_refresh_status.json`
- batch wrappers:
  `tmp/2026-06-16_paraview_movie_all_times_refresh/2026-06-16_movie_all_times_smoke.sbatch`
  and
  `tmp/2026-06-16_paraview_movie_all_times_refresh/2026-06-16_movie_all_times_refresh.sbatch`

### Movie-specific caveats

The representative time-series mirrors contained invalid reconstructed
temperature field files for multiple cases and intermediate times. ParaView's
OpenFOAM reader aborts when it encounters tokens like `-nan` inside those
files.

To make the movie path reusable without mutating the staged mirrors:

- the renderer screens candidate times for invalid numeric tokens in the
  required field files
- invalid times are skipped and recorded in the per-movie `status.json`
- if any times are skipped, the renderer stages a sanitized cache mirror under
  `cache/paraview_movie_cases/` that only symlinks valid times before opening
  the case in ParaView

This rule is currently most important for `temperature` movies. The final
durable batch rendered all `16` requested movies successfully, but several
temperature movies intentionally skip invalid reconstructed times and record
those skips in `status.json`.

### Movie packaging caveat

The current ParaView build on this cluster does not emit `.mp4` animations for
this workflow. It logs:

- `Failed to determine format for ... .mp4`

and may still segfault after writing the other artifacts.

The renderer therefore treats "MP4 file not created" as a packaging failure
and automatically retries `.ogv`.

For the current durable batch:

- all `16` movies rendered successfully
- all packaged movie files are `.ogv`
- the canonical frame sequences are also present

## Representative branch-arrow workflow

The branch-arrow still path is implemented in:

- `tools/extract/render_branch_velocity_arrow_images.py`

The current durable output root is:

- `figures/figures_rendered/paraview_velocity_arrows/`

Per-case output layout:

- `figures/figures_rendered/paraview_velocity_arrows/<source_id>/case_status.json`
- `figures/figures_rendered/paraview_velocity_arrows/<source_id>/<component>/png/`
- `figures/figures_rendered/paraview_velocity_arrows/<source_id>/<component>/svg/`
- `figures/figures_rendered/paraview_velocity_arrows/<source_id>/<component>/pdf/`
- `figures/figures_rendered/paraview_velocity_arrows/<source_id>/<component>/status.json`

Branch components:

- `upcomer`
- `downcomer`
- `heater`
- `cooler`

Rendering contract:

- latest-time only
- clip to the branch bounds derived from the same reusable patch metadata path
- slice at the z-reference plane
- convert cell `U` to point data with `CellDatatoPointData`
- compute `Umag = mag(U)` on point data
- orient arrows by `U`
- scale and color arrows by `Umag`
- use a fixed per-case magnitude range across the 4 branch stills
- cap glyph density for readability and reproducibility

The final durable batch rendered all `32` requested branch-arrow stills
successfully.

### Arrow-image quality tuning

The first durable arrow batch was technically complete but visually weak:

- branch geometry occupied too little of the frame
- glyphs were too dense and too small
- the neutral slice background was too opaque and washed out the arrows
- the raster export size was too modest for this glyph-heavy view family

The renderer was therefore updated and the full durable tree was refreshed on
`2026-06-16`.

Current default quality settings in
`render_branch_velocity_arrow_images.py` are:

- `maximum_number_of_sample_points = 900`
- `image_width = 3600`
- `image_height = 2400`
- `camera_scale_factor = 0.32`
- `glyph_scale_multiplier = 0.22`
- `base_opacity = 0.12`

The script also now:

- enables FXAA when the current ParaView build exposes that render-view flag
- uses a larger arrow tip and shaft resolution when those glyph-source
  properties are available
- records the effective image-resolution and framing parameters in each branch
  `status.json`

If future arrow outputs still look crowded or too sparse, tune these CLI
options first before changing the branch-selection logic:

- `--max-glyph-points`
- `--image-width`
- `--image-height`
- `--camera-scale-factor`
- `--glyph-scale-multiplier`
- `--base-opacity`

Representative refreshed artifact:

- `figures/figures_rendered/paraview_velocity_arrows/val_water_test_2_coarse_mesh_laminar/cooler/png/val_water_test_2_coarse_mesh_laminar_cooler_velocity_magnitude_arrows.png`

Representative refreshed status file:

- `figures/figures_rendered/paraview_velocity_arrows/val_water_test_2_coarse_mesh_laminar/cooler/status.json`

## Full representative batch

The tracked compute-safe batch wrapper used for the final durable run is:

- `tmp/2026-06-15_paraview_movie_and_arrow_smoke/2026-06-15_paraview_representative_movies_and_arrows.sbatch`

Important observations from that path:

- an early all-times reconstruction phase was originally included, but by the
  final durable run the staged representative mirrors already contained the
  required time series, so the working batch used the faster render-only path
- each `pvbatch` call is wrapped with `set +e` because ParaView still
  segfaults on shutdown after writing outputs
- the wrapper validates success by testing for the expected per-render
  `status.json` files after each invocation

Final durable totals:

- `16/16` movie status files reported `status: rendered`
- `32/32` branch-arrow status files reported `status: rendered`
