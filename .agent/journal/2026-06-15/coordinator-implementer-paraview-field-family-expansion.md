# Coordinator / Implementer Raw Journal

- date: `2026-06-15`
- agent role: `Coordinator / Implementer`
- task ID: `AGENT-075`
- branch/worktree: `no-HEAD`
- files inspected:
  - `AGENTS.md`
  - `.agent/BOARD.md`
  - `.agent/FILE_OWNERSHIP.md`
  - `.agent/ROLES.md`
  - `tools/AGENTS.override.md`
  - `staging/AGENTS.override.md`
  - `tools/extract/render_last_timestep_field_slices.py`
  - `tools/case_analysis_profiles.py`
  - `tools/analyze/build_ethan_run_postprocessing_package.py`
  - `tools/analyze/build_salt2_behavior_package.py`
  - `journals/2026-06/2026-06-10_ethan_runs.md`
  - `staging/render_inputs/val_salt_test_2_coarse_mesh_laminar/reconstructed_case/constant/polyMesh/boundary`
  - `tools/extract/stage_latest_time_field_reconstruction.py`
- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-15_AGENT-075.md`
  - `.agent/journal/2026-06-15/coordinator-implementer-paraview-field-family-expansion.md`
  - `tools/extract/render_last_timestep_field_slices.py`
  - `tools/extract/stage_latest_time_field_reconstruction.py`
  - `tools/extract/2026-06-15_paraview_field_render_workflow.md`
- commands run:
  - `rg -n "upcomer|downcomer|cooler|heater|pressure|p_rgh|total pressure|dynamic pressure|static pressure|leg" ...`
  - `sed -n '1,260p' tools/extract/render_last_timestep_field_slices.py`
  - `sed -n '1,260p' tools/case_analysis_profiles.py`
  - `sed -n '296,340p' journals/2026-06/2026-06-10_ethan_runs.md`
  - `sed -n '520,720p' tools/case_analysis_profiles.py`
  - `sed -n '1,220p' staging/render_inputs/val_salt_test_2_coarse_mesh_laminar/reconstructed_case/constant/polyMesh/boundary`
  - `python3.11 -m py_compile tools/extract/render_last_timestep_field_slices.py`
  - `mpiexec -n 1 "$TACC_PARAVIEW_OSMESA_BIN/pvbatch" tools/extract/render_last_timestep_field_slices.py --source-id val_salt_test_2_coarse_mesh_laminar --field velocity_x --component downcomer ...`
  - `mpiexec -n 1 "$TACC_PARAVIEW_OSMESA_BIN/pvbatch" tools/extract/render_last_timestep_field_slices.py --source-id val_salt_test_2_coarse_mesh_laminar --field pressure_total --component heater ...`
  - `mpiexec -n 1 "$TACC_PARAVIEW_OSMESA_BIN/pvbatch" tools/extract/render_last_timestep_field_slices.py --source-id val_salt_test_2_coarse_mesh_laminar --field pressure_static --component cooler ...`
  - `python3.11 tools/extract/stage_latest_time_field_reconstruction.py --source-id val_salt_test_2_coarse_mesh_laminar --field p ...`
  - `source jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh && export LD_LIBRARY_PATH="/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data:${LD_LIBRARY_PATH:-}" && unset FOAM_SIGFPE && python3.11 tools/extract/stage_latest_time_field_reconstruction.py --source-id val_salt_test_2_coarse_mesh_laminar --field p ...`
  - `mpiexec -n 1 "$TACC_PARAVIEW_OSMESA_BIN/pvbatch" tools/extract/render_last_timestep_field_slices.py --source-id val_salt_test_2_coarse_mesh_laminar --field pressure_dynamic --component upcomer ...`
  - `source jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh && export LD_LIBRARY_PATH="/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data:${LD_LIBRARY_PATH:-}" && unset FOAM_SIGFPE && python3.11 tools/extract/stage_latest_time_field_reconstruction.py --source-id val_salt_test_2_coarse_mesh_laminar --source-id viscosity_screening_salt_test_1_kirst_coarse_mesh --source-id viscosity_screening_salt_test_3_jin_coarse_mesh --source-id viscosity_screening_salt_test_4_jin_coarse_mesh --field p --status-path staging/render_inputs/2026-06-15_paraview_pressure_static_backfill_status.json`
  - `mpiexec -n 1 "$TACC_PARAVIEW_OSMESA_BIN/pvbatch" tools/extract/render_last_timestep_field_slices.py --source-id val_salt_test_2_coarse_mesh_laminar --source-id viscosity_screening_salt_test_1_kirst_coarse_mesh --source-id viscosity_screening_salt_test_3_jin_coarse_mesh --source-id viscosity_screening_salt_test_4_jin_coarse_mesh --field <temperature|velocity|velocity_x|velocity_y|velocity_z|pressure_static> --output-root figures_rendered/paraview_field_families`
- results or observations:
  - The Salt-family case profiles already provide a durable mapping from source
    ID to major spans and thermal patch roles, which is enough to define
    reusable component families like `heater`, `cooler`, and the left/right
    transport legs.
  - Existing reporting notes already treat `downcomer` as `pipeleg_right_*` and
    `upcomer` as `pipeleg_left_*`, which provides a repo-consistent naming rule
    for repeatable renderer selectors.
  - `render_last_timestep_field_slices.py` now supports:
    - `velocity_x`, `velocity_y`, `velocity_z` into `velocity_components/`
    - `pressure_static`, `pressure_dynamic`, `pressure_total` into `pressure/`
    - metadata-driven clip views for `upcomer`, `downcomer`, `cooler`, and
      `heater` by deriving axis-aligned clip bounds from OpenFOAM `polyMesh`
      wall-patch faces instead of manual camera or clip placement.
  - A live `pvbatch` smoke render for `velocity_x` on `downcomer` succeeded and
    wrote PNG/SVG/PDF plus a status JSON into
    `tmp/2026-06-15_paraview_field_family_smoke/velocity_components/downcomer/`.
    ParaView still segfaulted afterward during shutdown, which matches the
    previously accepted behavior for this render family.
  - Pressure-family smoke renders initially failed for two distinct reasons:
    - the staged reconstructed render input only contained `T` and `U`, not `p`
    - the existing latest-time field staging helper uses `reconstructPar
      -newTimes`, which prevents backfilling a newly requested field into an
      already-present latest-time mirror
  - `stage_latest_time_field_reconstruction.py` now defaults to backfilling
    fields into the latest-time mirror and materializes local writable copies of
    `constant/` and `system/` instead of symlinking them. That avoids both:
    - the `-newTimes` no-op when a time directory already exists
    - OpenFOAM 13 write failures such as missing writable `constant/fvMesh`
      paths during pressure reconstruction
  - Reconstructing `p` under the incompatible `openfoam/12` module failed, but
    the repo's documented OpenFOAM 13 bootstrap plus the shared
    `libRCWallBC.so` path succeeded:
    - env script:
      `jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh`
    - extra library dir:
      `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data`
  - Representative successful validations now cover:
    - `velocity_x` on `downcomer`
    - `pressure_static` on `cooler`
    - `pressure_total` on `heater`
    - `pressure_dynamic` on `upcomer`
  - All four of those runs wrote PNG/SVG/PDF outputs plus `failed_count: 0`
    status JSONs under `tmp/2026-06-15_paraview_field_family_smoke/`.
  - User explicitly asked not to rely on the derived dynamic-pressure/total-pressure
    path for the durable batch output. The production render pass therefore
    excluded `pressure_dynamic` and `pressure_total` and only emitted the
    non-derived field family:
    - `temperature`
    - `velocity`
    - `velocity_x`
    - `velocity_y`
    - `velocity_z`
    - `pressure_static`
  - Backfilled `p` successfully for the four active Salt-family ParaView cases
    into their staged reconstructed mirrors, with tracked status in:
    - `staging/render_inputs/2026-06-15_paraview_pressure_static_backfill_status.json`
  - Batch-rendered the durable non-derived field family for those same four
    cases into:
    - `figures_rendered/paraview_field_families/`
  - Verified aggregate render success from:
    - `figures_rendered/paraview_field_families/last_timestep_temperature_slice_status.json`
    - `figures_rendered/paraview_field_families/last_timestep_velocity_slice_status.json`
    - `figures_rendered/paraview_field_families/velocity_components/last_timestep_velocity_x_slice_status.json`
    - `figures_rendered/paraview_field_families/velocity_components/last_timestep_velocity_y_slice_status.json`
    - `figures_rendered/paraview_field_families/velocity_components/last_timestep_velocity_z_slice_status.json`
    - `figures_rendered/paraview_field_families/pressure/last_timestep_pressure_static_slice_status.json`
    Each one reports `case_count: 4`, `rendered_count: 4`, `failed_count: 0`.
  - User then corrected the canonical durable output location to live under
    `figures/figures_rendered/` rather than the repo-root `figures_rendered/`
    folder. I left the earlier root-level batch untouched and reran the
    requested component-scoped families under:
    - `figures/figures_rendered/paraview_field_families/upcomer/`
    - `figures/figures_rendered/paraview_field_families/downcomer/`
    - `figures/figures_rendered/paraview_field_families/cooler/`
    - `figures/figures_rendered/paraview_field_families/heater/`
    - `figures/figures_rendered/paraview_field_families/velocity_components/<component>/`
  - The canonical component batch intentionally skipped all pressure families.
    Verified status JSON for every component/field combination now reports
    `case_count: 4`, `rendered_count: 4`, `failed_count: 0`:
    - `upcomer`: `temperature`, `velocity`, `velocity_x`, `velocity_y`, `velocity_z`
    - `downcomer`: `temperature`, `velocity`, `velocity_x`, `velocity_y`, `velocity_z`
    - `cooler`: `temperature`, `velocity`, `velocity_x`, `velocity_y`, `velocity_z`
    - `heater`: `temperature`, `velocity`, `velocity_x`, `velocity_y`, `velocity_z`
  - Added a durable dated workflow note at
    `tools/extract/2026-06-15_paraview_field_render_workflow.md` covering:
    - the compute-node ParaView environment and `pvbatch` launch pattern
    - the canonical `figures/figures_rendered/` destination
    - the known post-write ParaView MPI shutdown segfault and how to validate
      results from status JSON instead of the raw exit code
    - the OpenFOAM 13 pressure-backfill bootstrap and the writable
      `constant/`/`system/` staging fix
    - the recommendation to avoid derived pressure families for the current
      fixed-pressure figure workflow
- contradictions or unresolved issues:
  - ParaView still segfaults after writing the artifacts on MPI shutdown. This
    remains an accepted caveat for the render family; success must be judged by
    written artifacts and the status JSON payloads rather than the raw process
    exit code.
- next steps:
  - Reuse the canonical `figures/figures_rendered/paraview_field_families/`
    trees as the input set for the next video-assembly step.

## Follow-on layout normalization

- user request:
  - normalize the canonical component-view tree so field families sit between
    the component and file-type directories
  - place the velocity component outputs alongside the scalar families instead
    of under a separate `velocity_components/` subtree
- files changed:
  - `.agent/status/2026-06-15_AGENT-075.md`
  - `.agent/journal/2026-06-15/coordinator-implementer-paraview-field-family-expansion.md`
  - `tools/extract/render_last_timestep_field_slices.py`
  - `tools/extract/2026-06-15_paraview_field_render_workflow.md`
  - `figures/figures_rendered/paraview_field_families/**`
- commands run:
  - `find figures/figures_rendered/paraview_field_families -maxdepth 4 -type f | sort`
  - `rg -n "velocity_components/|paraview_field_families/(upcomer|downcomer|cooler|heater)/" .`
  - `python3.11 -m py_compile tools/extract/render_last_timestep_field_slices.py`
  - shell migration of the existing canonical component-view artifacts into:
    - `figures/figures_rendered/paraview_field_families/<component>/temperature/**`
    - `figures/figures_rendered/paraview_field_families/<component>/velocity/**`
    - `figures/figures_rendered/paraview_field_families/<component>/x_vel/**`
    - `figures/figures_rendered/paraview_field_families/<component>/y_vel/**`
    - `figures/figures_rendered/paraview_field_families/<component>/z_vel/**`
- results or observations:
  - no new ParaView rendering was required because the x/y/z component images
    already existed; the task was a canonical routing and migration change
  - the renderer now writes future component views directly to
    `<component>/<field>/<filetype>/`
  - the current public-facing field names are:
    - `temperature`
    - `velocity`
    - `x_vel`
    - `y_vel`
    - `z_vel`
  - the canonical status JSON files moved with the artifacts and were updated
    so their internal `status_path` and per-case figure paths point at the new
    tree

## Representative movies and branch arrows

- files changed:
  - `.agent/status/2026-06-15_AGENT-075.md`
  - `.agent/journal/2026-06-15/coordinator-implementer-paraview-field-family-expansion.md`
  - `tools/extract/render_representative_field_movies.py`
  - `tools/extract/render_branch_velocity_arrow_images.py`
  - `tools/extract/stage_latest_time_field_reconstruction.py`
  - `tools/extract/2026-06-15_paraview_field_render_workflow.md`
  - `tmp/2026-06-15_paraview_movie_and_arrow_smoke/**`
  - `figures/figures_rendered/paraview_movies/**`
  - `figures/figures_rendered/paraview_velocity_arrows/**`
- commands run:
  - `python3.11 -m py_compile tools/extract/render_representative_field_movies.py`
  - `python3.11 -m py_compile tools/extract/render_branch_velocity_arrow_images.py`
  - `python3.11 -m py_compile tools/extract/stage_latest_time_field_reconstruction.py`
  - `ssh login3.ls6.tacc.utexas.edu "cd ... && sbatch --parsable tmp/2026-06-15_paraview_movie_and_arrow_smoke/2026-06-15_movie_smoke_debug.sbatch"`
  - `ssh login3.ls6.tacc.utexas.edu "cd ... && sbatch --parsable tmp/2026-06-15_paraview_movie_and_arrow_smoke/2026-06-15_arrow_smoke_debug.sbatch"`
  - `ssh login3.ls6.tacc.utexas.edu "cd ... && sbatch --parsable tmp/2026-06-15_paraview_movie_and_arrow_smoke/2026-06-15_paraview_representative_movies_and_arrows.sbatch"`
  - `python3.11 - <<'PY' ...` aggregation over `figures/figures_rendered/paraview_movies/*/*/status.json` and `figures/figures_rendered/paraview_velocity_arrows/*/*/status.json`
- results or observations:
  - Added `render_representative_field_movies.py` for 5-panel overview/upcomer/downcomer/heater/cooler field movies across the 8 representative cases for `temperature` and `velocity_y`.
  - Added `render_branch_velocity_arrow_images.py` for last-timestep branch-only velocity-magnitude arrow stills, using `CellDatatoPointData` plus `Glyph` so arrows orient by `U` and scale/color by `|U|`.
  - Extended `stage_latest_time_field_reconstruction.py` with `--all-times` so staged reconstructed mirrors can hold full time series instead of only latest time.
  - The representative staged mirrors already existed by the time the final batch ran, so the successful durable batch used the faster render-only path from those mirrors instead of repeating all-times reconstruction.
  - The movie renderer now screens staged reconstructed times for invalid numeric tokens before opening them in ParaView. When invalid field files are found, it stages a sanitized cache mirror with only valid times and records the skipped times in the per-movie `status.json`.
  - This screening was required in practice. Temperature movies skipped invalid reconstructed times for:
    - `viscosity_screening_salt_test_1_jin_coarse_mesh`: `3227`, `3228`
    - `val_salt_test_2_coarse_mesh_laminar`: `1722`, `1723`, `1724`
    - `viscosity_screening_salt_test_3_jin_coarse_mesh`: `2512`, `2513`, `2514`
    - `viscosity_screening_salt_test_4_jin_coarse_mesh`: `2081`, `2082`
    - `val_water_test_1_coarse_mesh_laminar`: `3192`, `3194`, `5271`, `5272`, `5274`
    - `val_water_test_2_coarse_mesh_laminar`: `2434`, `2435`, `3976`, `3978`, `3980`
    - `val_water_test_3_coarse_mesh_laminar`: `2252`, `2253`, `3724`, `3725`, `3726`, `3727`, `3728`
    - `val_water_test_4_coarse_mesh_laminar`: `1465`, `1466`, `1467`, `2538`, `2540`, `2541`
  - ParaView on this cluster build would not emit `.mp4` animations and only logged `Failed to determine format ... .mp4` without raising a Python exception. The renderer was hardened to treat "MP4 file not created" as failure and retry `.ogv`.
  - Compute-node smoke validations succeeded after those fixes:
    - movie smoke job `3234697`: Salt 2 `temperature` movie rendered with `status: rendered`, `frame_count: 2`, `movie_format: ogv`
    - arrow smoke job `3234715`: Water 2 `cooler` arrow still rendered with PNG/SVG/PDF and `status: rendered`
  - Final durable render-only batch job `3234770` completed successfully and produced:
    - `16/16` rendered movie status files under `figures/figures_rendered/paraview_movies/`
    - `32/32` rendered branch-arrow status files under `figures/figures_rendered/paraview_velocity_arrows/`
    - `48` durable movie metadata/movie files total
    - `136` durable arrow metadata/still files total
- contradictions or unresolved issues:
  - The raw `pvbatch` processes still segfault on shutdown after writing outputs. The Slurm wrappers therefore must judge success from written artifacts plus the per-render status JSON.
  - The delivered movie format on this environment is `.ogv`, not `.mp4`.
- next steps:
  - Use the completed representative movie and branch-arrow trees to choose the next user-facing video composition step instead of doing more raw ParaView extraction.

## June 16 all-times representative movie refresh

- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-15_AGENT-075.md`
  - `.agent/journal/2026-06-15/coordinator-implementer-paraview-field-family-expansion.md`
  - `imports/2026-06-16_paraview_movie_all_times_refresh.json`
  - `tools/extract/stage_latest_time_field_reconstruction.py`
  - `tools/extract/render_representative_field_movies.py`
  - `tools/extract/2026-06-15_paraview_field_render_workflow.md`
  - `tmp/2026-06-16_paraview_movie_all_times_refresh/**`
- commands run:
  - `python3.11 -m py_compile tools/extract/stage_latest_time_field_reconstruction.py`
  - `python3.11 -m py_compile tools/extract/render_representative_field_movies.py`
  - `ssh login3.ls6.tacc.utexas.edu "cd ... && sbatch --parsable tmp/2026-06-16_paraview_movie_all_times_refresh/2026-06-16_movie_all_times_smoke.sbatch"`
  - `ssh login3.ls6.tacc.utexas.edu "cd ... && sbatch --parsable tmp/2026-06-16_paraview_movie_all_times_refresh/2026-06-16_movie_all_times_refresh.sbatch"`
  - `ssh login3.ls6.tacc.utexas.edu "squeue -j 3236147,3236160 ..."`
  - `ssh login3.ls6.tacc.utexas.edu "sacct -j 3236147,3236160 ..."`
- results or observations:
  - The registered representative source roots are not equally rich. Salt 2 in
    particular only exposed `0` plus the early retained times through `1724`
    at its registered source root, but the continuation-stage case under
    `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/` exposes a
    longer retained window through `8602`.
  - Salt 1 Jin and Salt 4 Jin also have richer continuation-stage trees than
    their registered source roots.
  - `stage_latest_time_field_reconstruction.py` now resolves the richest
    available source root by comparing the registered root with matching
    continuation-stage candidates under `jadyn_runs/**/case_stage/`.
  - The June 16 Salt 2 smoke run successfully switched the staged render-input
    mirror to the continuation tree and reconstructed all retained times:
    `0`, `1720-1724`, `5178-5182`, and `8598-8602`.
  - `render_representative_field_movies.py` now supports explicit high-res
    PNG-frame rendering with:
    - `--frames-only`
    - `--image-width`
    - `--image-height`
    and it uses the staged/source time list for frame selection so `t=0` can
    be requested even when ParaView's scene timestep list omits it.
  - The first June 16 smoke submission failed before reconstruction because the
    OpenFOAM 13 bootstrap is not safe to source under `set -euo pipefail`.
    The batch wrappers were corrected to source the bootstrap outside strict
    pipefail mode.
  - The second smoke submission reconstructed Salt 2 correctly but failed
    before rendering because the OpenFOAM environment left `gcc/13.2.0` and
    `impi/21.12` loaded, while the current ParaView build requires
    `gcc/11.2.0`, `impi/19.0.9`, and `paraview_osmesa/5.13.3`. The wrappers
    were corrected to `module purge` and reload the ParaView-compatible toolchain
    before invoking `pvbatch`.
  - Live jobs after those fixes:
    - `3236147`: Salt 2 smoke, frames-only representative movie refresh
    - `3236160`: full 8-case frames-only representative movie refresh
- contradictions or unresolved issues:
  - At the end of this turn, the Salt 2 smoke render and the full 8-case
    frames-only refresh were still running on the cluster, so the updated
    representative movie `status.json` payloads had not yet been rewritten.
  - The staging-side refresh for Salt 2 is already confirmed from
    `staging/render_inputs/2026-06-16_paraview_movie_all_times_refresh_status.json`,
    but the render-side frame counts still need confirmation from the live job
    outputs.
- next steps:
  - Let jobs `3236147` and `3236160` finish.
  - Confirm refreshed representative movie status JSON payloads now contain
    explicit `frame_times` and the expected higher frame counts.
