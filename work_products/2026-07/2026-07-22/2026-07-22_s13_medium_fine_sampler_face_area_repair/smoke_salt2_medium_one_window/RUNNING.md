---
provenance:
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
tags: [s13, smoke, medium-fine, face-area-vector]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22.md
task: TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22
date: 2026-07-22
role: Scheduler smoke handoff
type: handoff
status: complete
---
# S13 Salt2 Medium One-Window Smoke

This clean smoke package runs only:

- `case_id=salt_2`
- `mesh_level=medium`
- `max_windows=1`

The purpose is to prove generated exchange-interface rows carry
`area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2` before any full
six-case rerun.

Submitted Slurm job: `3311109`.

Latest observed state: `COMPLETED`, exit code `0:0`, on `c318-018`, start
`2026-07-22T11:44:59`, end `2026-07-22T11:49:50`.

Scheduler check:

```bash
squeue -j 3311109
sacct -j 3311109 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList
```

On completion, inspect:

- `summary.json`
- `sampling_error_log.csv`
- `medium_fine_exact_label_qoi_rows.csv`
- `faces/salt_2_medium_exchange_interface_faces.csv`

Inspection result:

- `summary.json`: `exact_label_qoi_rows=4`, `sampling_error_rows=0`,
  `terminal_window_reduction_rows=1`, and `native_solver_outputs_mutated=false`.
- `faces/salt_2_medium_exchange_interface_faces.csv`: contains
  `area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2`.
- `medium_fine_exact_label_qoi_rows.csv`: contains `Q_wall_W`,
  `mdot_exchange_positive_outward_proxy_kg_s`, `tau_recirc_proxy_s`, and
  `wall_core_bulk_temperature_contrast_K`.
- `logs/slurm-3311109.err`: empty at closeout.

This smoke package succeeded. Full six-case Slurm rerun must be a separate
claimed row.
