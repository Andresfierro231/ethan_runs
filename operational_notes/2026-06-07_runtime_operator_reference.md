# 2026-06-07 Runtime Operator Reference

This note records the runtime facts that were rechecked repeatedly during the June 7 reporting and rendering pass. Future agents should start here before probing Python, ParaView, or node context again.

## Current node context

- Verified on 2026-06-07 from `hostname`: `login3.ls6.tacc.utexas.edu`
- Safe login-node work:
  - read/write notes and scripts
  - `py_compile`
  - light report generation with the working Matplotlib Python
- Compute-node work still preferred or required for:
  - ParaView `pvbatch` rendering with OSMesa
  - larger OpenFOAM reconstruction/postprocessing runs
  - any workflow that depends on loaded TACC modules rather than the plain login environment

## Known Python interpreters

- `python`
  - verified as `Python 3.9.7`
  - executable path observed from `sys.executable`: `/usr/bin/python`
  - verified working Matplotlib version: `3.4.3`
  - use this interpreter for the local Matplotlib report builders unless a script documents a different requirement
- `python3.11`
  - verified as `Python 3.11.9`
  - does **not** currently have `matplotlib` importable in this workspace context
  - still useful for:
    - stdlib-only utilities
    - `py_compile`
    - helper scripts that do not need Matplotlib

## ParaView / rendering environment

- Verified working compute-node module load for ParaView batch rendering:
  - `module load gcc/11.2.0 impi/19.0.9 paraview_osmesa/5.13.3`
- Verified launcher pattern:
  - `unset TACC_PARAVIEW_BIN`
  - `$TACC_PARAVIEW_OSMESA_BIN/pvbatch tools/extract/render_last_timestep_temperature_slices.py ...`
- Verified successful June 7 smoke jobs after the renderer fixes:
  - `3214869` for `viscosity_screening_salt_test_1_kirst_coarse_mesh`
  - `3214870` for `val_salt_test_2_coarse_mesh_laminar`
- Current machine-readable slice status:
  - `figures/last_timestep_temperature_slice_status.json`

## OpenFOAM reconstruction / postprocessing notes

- The reconstruction-first render path remains the defensible path for ParaView figures:
  - stage local mirrored cases
  - reconstruct latest-time fields locally
  - render one case per `pvbatch` process
- `tools/extract/stage_latest_time_reconstruction.py` is still part of the approved slice workflow.
- The transient axial package is still blocked on a known reconstructed-`T` readability issue in `foamPostProcess`.
  - Current failure family: scalar-token parse failure while reading reconstructed `T`
  - Treat this as a case/postprocessing readability issue, not as evidence that the source `wallHeatFlux.dat` histories are unusable

## Figure convention

- Use typed figure subfolders everywhere:
  - `figures/png`
  - `figures/svg`
  - `figures/pdf`
- Do not reintroduce flat generated figure files in report roots or the top-level `figures/` root.
- The last-timestep temperature slices now use the reference `z` plane rather than the old `x` plane.

## Known good starting points

- Local Matplotlib reports:
  - run with `python`
- Stdlib script validation:
  - run with `python3.11`
- ParaView smoke or batch render:
  - use the `staging/render_jobs/*.sbatch` patterns and the OSMesa module load above
- Laptop transfer of report products and reconstructed cases:
  - use `tools/publish/download_results_to_laptop.sh`

## Recheck only if one of these changes

- hostname moves off the LS6 login nodes
- `python --version` changes away from `3.9.7`
- Matplotlib import stops working in `/usr/bin/python`
- ParaView module names or TACC environment variables change
- the reconstructed-`T` failure is repaired and the transient axial package workflow is materially different
