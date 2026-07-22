# Salt2 Cell VTK Smoke Scheduler Handoff

Task: `TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT2-SMOKE-2026-07-21`

Job: `3308472`

State: `FAILED`

Exit code: `13:0`

Command: `ssh login3 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/scripts/submit_salt2_cell_vtk_smoke.sbatch'`

Expected output: `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/vtk/salt_2_cell_fields.vtk`

Artifact validation: `pass`

Terminal condition: validation report passes or Slurm logs record failure. Killing the job is safe for native outputs because all writes are task-local.
