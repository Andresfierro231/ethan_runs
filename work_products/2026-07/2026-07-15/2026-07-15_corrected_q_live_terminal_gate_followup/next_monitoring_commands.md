---
provenance:
  - operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md
  - work_products/2026-07/2026-07-15/2026-07-15_corrected_q_live_terminal_gate_followup/scheduler_snapshot.csv
tags: [salt-q-perturbation, scheduler, terminal-harvest]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_corrected_q_live_terminal_gate_followup/README.md
task: AGENT-408
date: 2026-07-15
role: cfd-pp/Coordinator/Writer
type: work_product
status: complete
---
# Next Monitoring Commands

Run these from the repo root.

```bash
squeue -j 3293924,3295438,3295989,3295990,3295991
sacct -j 3293924,3295438,3295989,3295990,3295991 --format=JobID,JobName,Partition,State,Elapsed,ExitCode,Submit,Start,End,NodeList -P
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.out
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.err
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt2_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt2_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q
tail -80 jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_corrected_q
```

Only after `3293924` and `3293924.0` through `.3` are terminal:

```bash
sacct -j 3295438 --format=JobID,JobName,Partition,State,Elapsed,ExitCode,Submit,Start,End,NodeList -P
tail -80 work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/slurm-saltq_s24_sel_harv-3295438.out
tail -80 work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/slurm-saltq_s24_sel_harv-3295438.err
```

Do not infer admission from `COMPLETED`. Admission still requires terminal harvest evidence plus an operating-point convergence/stationarity gate.
