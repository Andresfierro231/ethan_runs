# Salt 1 Nominal Continuation Candidate

Date: `2026-07-08`
Task: `AGENT-206`

This campaign stages a single corrected Salt 1 nominal continuation from the
June 25 `salt1_jin_basecont` candidate.

Source case:

`jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt1_jin_basecont/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation`

Target case:

`runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation`

The source tree contains retained processor data through `4026.15625 s` and
ended cleanly via the original convergence monitor. This staged continuation
keeps the same nominal operating point and `endTime 10000`, but changes the
copied `system/functions` convergence monitor so it logs a diagnostic message
and does not call `stopAt(writeNow)`.

The launcher requests one 64-rank Slurm job. It is not packable after launch;
additional cases must be submitted as separate jobs or staged into a separate
packed allocation.

Submission:

- Job: `3282992`
- Name: `salt1_nom_cont`
- Submitted: `2026-07-08` via `login3.ls6.tacc.utexas.edu`
- State at submission check: `PENDING (Priority)`
- Requested resources: `NuclearEnergy`, account `ASC23046`, `1` node,
  `64` tasks, `120:00:00`
