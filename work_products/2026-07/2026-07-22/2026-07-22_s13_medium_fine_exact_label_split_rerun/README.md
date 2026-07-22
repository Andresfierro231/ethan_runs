---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/smoke_salt2_medium_one_window/summary.json
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
tags: [work-product, s13, medium-fine, exact-label, split-rerun]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-EXACT-LABEL-SPLIT-RERUN-2026-07-22.md
  - .agent/journal/2026-07-22/s13-medium-fine-exact-label-split-rerun.md
task: TODO-S13-MEDIUM-FINE-EXACT-LABEL-SPLIT-RERUN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Medium/Fine Exact-Label Split Rerun

This package runs the repaired sampler after the Salt2/medium one-window smoke
passed. The full medium/fine sampling is split into one Slurm array element per
case/mesh:

- `salt_2 medium`
- `salt_2 fine`
- `salt_3 medium`
- `salt_3 fine`
- `salt_4 medium`
- `salt_4 fine`

Each element writes to a unique `outputs/<case>_<mesh>/` directory. This avoids
shared-output overwrite and allows completed rows to be aggregated only from
terminal successful elements.

## Guardrails

No native OpenFOAM output mutation, registry/admission mutation, solver run,
OpenFOAM postProcess, mesh/GCI disposition, source/property/Qwall release,
coefficient admission, final score, S11/S12/S13/S15/S6 trigger, or proxy
substitution is allowed here.

Mesh/GCI remains a separate next row after complete exact-label rows exist.

## Result

Slurm array `3311146[0-5]` completed successfully for all six case/mesh pairs.
The aggregate outputs are:

- `aggregated_exact_label_qoi_rows.csv`: `72` rows
- `aggregated_terminal_window_reductions.csv`: `18` rows
- `split_job_terminal_summary.csv`: `6/6` terminal successful case/mesh rows
- `mesh_gci_unlock_gate.csv`: all four QOIs have medium/fine exact-label rows
- `summary.json`: `split_exact_label_rows_complete_mesh_gci_disposition_unlocked_no_admission`

This package unlocks a separate mesh/GCI disposition row. It does not run that
disposition and does not admit any model form or coefficient.
