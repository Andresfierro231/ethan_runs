# AGENT-098 Raw Journal — ParaView Accounting And Laptop Download Docs

- date: `2026-06-22`
- role: `Coordinator / Implementer`
- task ID: `AGENT-098`
- purpose:
  - document the current accepted handling of ParaView's post-write
    `ExitCode=11`
  - document the practical laptop download path for local ParaView inspection,
    including what to copy and representative sizes
- files inspected:
  - `.agent/BOARD.md`
  - `README.md`
  - `tools/AGENTS.override.md`
  - `staging/AGENTS.override.md`
  - `tools/extract/2026-06-15_paraview_field_render_workflow.md`
  - `tools/publish/download_results_to_laptop.sh`
  - `operational_notes/06-26/16/2026-06-16_ethan_box_upload_plan.md`
  - `tmp/2026-06-16_paraview_movie_all_times_refresh/2026-06-16_movie_all_times_refresh.sbatch`
  - `staging/render_jobs/2026-06-15_paraview_cell_association_refresh.sbatch`
- plan:
  - add a discoverable summary to `README.md`
  - add the explicit Slurm-accounting rule to the ParaView workflow note
  - capture the fuller laptop-download instructions and representative sizes in
    a dated operational note

- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-22_AGENT-098.md`
  - `.agent/journal/2026-06-22/coordinator-implementer-paraview-accounting-and-download-docs-AGENT-098.md`
  - `README.md`
  - `tools/extract/2026-06-15_paraview_field_render_workflow.md`
  - `operational_notes/06-26/22/2026-06-22_paraview_download_and_slurm_accounting.md`

- commands run:
  - `sed -n '600,690p' tools/extract/2026-06-15_paraview_field_render_workflow.md`
  - `sed -n '1,220p' tools/publish/download_results_to_laptop.sh`
  - `sed -n '1,220p' operational_notes/06-26/16/2026-06-16_ethan_box_upload_plan.md`
  - `du -sh staging/render_inputs/viscosity_screening_salt_test_1_jin_coarse_mesh/reconstructed_case staging/render_inputs/val_salt_test_2_coarse_mesh_laminar/reconstructed_case staging/render_inputs/val_water_test_1_coarse_mesh_laminar/reconstructed_case staging/render_inputs/viscosity_screening_salt_test_4_jin_coarse_mesh/reconstructed_case`
  - `du -sh figures/figures_rendered/paraview_movies/val_salt_test_2_coarse_mesh_laminar figures/figures_rendered/paraview_movies/val_water_test_1_coarse_mesh_laminar figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar figures/figures_rendered/paraview_field_families`
  - `sacct -j 3237163 --format=JobID,JobName%30,State,ExitCode`

- results or observations:
  - The clean scheduler-accounting answer is already implicit in the wrappers:
    `pvbatch` can die after writing files, so the durable status payloads are
    the real success criterion.
  - The laptop helper is already the right transfer primitive for local
    ParaView use, but that fact was not surfaced clearly enough in repo-facing
    docs.
  - The practical local download size per reconstructed case is a few GiB, not
    tens of GiB, if the scope stays at `reconstructed_case` plus lightweight
    metadata.
  - The helper still excludes the newer `figures/figures_rendered/paraview_*`
    trees; that is now documented explicitly rather than left implicit.
