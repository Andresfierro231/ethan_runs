---
provenance:
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/smoke_salt2_medium_one_window/summary.json
tags: [s13, medium-fine, exact-label, split-rerun, slurm]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-EXACT-LABEL-SPLIT-RERUN-2026-07-22.md
  - .agent/journal/2026-07-22/s13-medium-fine-exact-label-split-rerun.md
task: TODO-S13-MEDIUM-FINE-EXACT-LABEL-SPLIT-RERUN-2026-07-22
date: 2026-07-22
role: Scheduler/Implementer/Tester/Writer
type: handoff
status: complete
---
# S13 Medium/Fine Exact-Label Split Rerun

This package ran the smoke-passed S13 sampler contract over six isolated
case/mesh outputs:

- `salt_2` / `medium`
- `salt_2` / `fine`
- `salt_3` / `medium`
- `salt_3` / `fine`
- `salt_4` / `medium`
- `salt_4` / `fine`

Canonical wrapper:

`work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/run_split_exact_label_sampler.sbatch`

Canonical array:

- `3311146`
- all six elements `COMPLETED 0:0`
- canonical outputs under `outputs/<case>_<mesh>/`

Inspection artifacts:

- `summary.json`
- `split_job_terminal_summary.csv`
- `aggregated_exact_label_qoi_rows.csv`
- `aggregated_terminal_window_reductions.csv`
- `mesh_gci_unlock_gate.csv`

Result:

- `6/6` case-meshes terminal successful.
- `72` aggregate exact-label QOI rows.
- `18` terminal-window reduction rows.
- `0` sampling-error rows in successful outputs.
- `mesh_gci_disposition_unlocked=true`.
- `mesh_gci_disposition_run_here=false`.

Duplicate array `3311175` was canceled after the canonical array was already
running. The duplicate wrapper
`run_split_medium_fine_exact_label_sampler.sbatch` and the `split_runs/`
directory are partial/noncanonical and must not be used for mesh/GCI,
production harvest, or admission evidence.

Mesh/GCI may now be opened only as a separate row.
