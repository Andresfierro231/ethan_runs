# ParaView Slurm Accounting And Laptop Download Notes

Date: `2026-06-22`
Task: `AGENT-098`

## Purpose

Capture the current practical guidance for two recurring ParaView questions:

- how to account for the known post-write `pvbatch` shutdown `ExitCode=11`
- how to download selected OpenFOAM results to a local computer for ParaView
  inspection without mirroring the whole workspace

## Post-write `ExitCode=11` policy

Observed behavior:

- ParaView `pvbatch` can segfault on shutdown with `ExitCode=11` after the
  intended render outputs have already been written.
- For this workflow, the raw ParaView exit code is therefore not sufficient to
  classify the render as success or failure.

Current trusted wrapper pattern:

- run `pvbatch` under `set +e`
- capture the raw return code for logging
- validate the expected durable render artifacts after the ParaView process
  exits
- fail the Slurm batch only when the durable output validation fails

Current durable success signal:

- the expected per-render `status.json` files exist
- each status payload reports `status: rendered`
- any extra bounded checks for the render family also pass, such as minimum
  frame counts for representative movies

Why this is the cleaner Slurm accounting:

- it records the condition that actually matters to downstream users:
  whether the render artifacts are complete and valid
- it avoids polluting `sacct` with false `FAILED 11:0` outcomes when ParaView
  crashed only during shutdown cleanup
- it still preserves a hard failure when the expected render outputs are
  missing, malformed, or explicitly marked failed

Concrete repo examples:

- workflow note:
  `tools/extract/2026-06-15_paraview_field_render_workflow.md`
- representative all-times movie wrapper:
  `tmp/2026-06-16_paraview_movie_all_times_refresh/2026-06-16_movie_all_times_refresh.sbatch`
- cell-association refresh wrapper:
  `staging/render_jobs/2026-06-15_paraview_cell_association_refresh.sbatch`

Concrete verified outcome:

- `sacct -j 3237163 --format=JobID,JobName,State,ExitCode`
- job `3237163` (`pv_movie_refresh`) reported `COMPLETED 0:0`

## Local download workflow

Current helper:

- `tools/publish/download_results_to_laptop.sh`

Intent:

- run it from a personal laptop or workstation
- connect back to LS6 over `ssh` and `rsync`
- pull only the practical subset needed for local review instead of staging a
  full workspace mirror

Do not use Slurm for this path:

- this is a client-side transfer workflow, not a cluster batch workflow
- the script should be run on the local machine that will receive the files
- no `sbatch` wrapper is required for the normal laptop-download case

Usage:

```bash
./tools/publish/download_results_to_laptop.sh DEST_DIR [SOURCE_ID ...]
```

Example:

```bash
./tools/publish/download_results_to_laptop.sh ~/Downloads/ethan_runs_laptop \
  viscosity_screening_salt_test_1_kirst_coarse_mesh \
  val_salt_test_2_coarse_mesh_laminar
```

Environment overrides:

- `REMOTE_USER`
- `REMOTE_HOST`
- `REMOTE_ROOT`
- `RSYNC_FLAGS`

Default remote target:

- `andresfierro231@login3.ls6.tacc.utexas.edu:/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

## What to download

Minimum payload to open a case locally in ParaView:

- `staging/render_inputs/<source_id>/reconstructed_case`

Recommended accompanying payload:

- `work_products/<source_id>`
- shared report packages already listed in the helper
- `registry/case_registry.csv`

What the current helper already pulls:

- `registry/case_registry.csv`
- `figures/last_timestep_temperature_slice_status.json`
- `figures/png`
- `figures/svg`
- `figures/pdf`
- selected dated report packages
- `staging/render_inputs/<source_id>/reconstructed_case`
- `work_products/<source_id>`

What the helper does not currently pull:

- `figures/figures_rendered/paraview_movies/**`
- `figures/figures_rendered/paraview_velocity_arrows/**`
- `figures/figures_rendered/paraview_field_families/**`

If those rendered ParaView outputs are also wanted locally, extend the helper
or issue additional `rsync` commands for those trees.

## Representative sizes

Observed reconstructed-case sizes:

- `viscosity_screening_salt_test_1_jin_coarse_mesh`: about `2.5G`
- `val_salt_test_2_coarse_mesh_laminar`: about `2.5G`
- `val_water_test_1_coarse_mesh_laminar`: about `1.7G`
- `viscosity_screening_salt_test_4_jin_coarse_mesh`: about `2.3G`

Observed generated-output sizes:

- one representative movie tree:
  `figures/figures_rendered/paraview_movies/val_salt_test_2_coarse_mesh_laminar`
  is about `5.2M`
- one representative arrow tree:
  `figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar`
  is about `102M`
- full `figures/figures_rendered/paraview_field_families` is about `895M`

Observed work-product sizes:

- representative `work_products/<source_id>` trees here are tiny, about `14K`

## Practical recommendation

For interactive local ParaView review:

- start with one or two `SOURCE_ID`s
- download only the reconstructed cases plus matching `work_products`
- add rendered figure trees only if you specifically want the prebuilt movie,
  arrow, or field-family outputs

For local reruns rather than viewing:

- the helper is not a full solver-case export
- rerunning OpenFOAM locally would require the complete runnable case tree, not
  just `reconstructed_case`
- that is a larger transfer and should be scoped explicitly before copying
