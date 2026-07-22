# Salt3/Salt4 Cell VTK Matrix Scheduler Handoff

Task: `TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT3-SALT4-MATRIX-2026-07-21`

Job: `3308527`

State: `COMPLETED`

Exit code: `0:0`

Command: `ssh login3.ls6.tacc.utexas.edu 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch --parsable work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/scripts/submit_salt3_salt4_cell_vtk_matrix.sbatch'`

Expected outputs: `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/vtk/salt_3_cell_fields.vtk;work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/vtk/salt_4_cell_fields.vtk`

Artifact status: `pass`

Terminal condition: both validation rows pass or Slurm logs record failure. Killing the job is safe for native outputs because all writes are task-local.
