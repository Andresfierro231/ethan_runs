---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/sampling_error_log.csv
tags: [s13, sampler-monitor, duplicate-job, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-SAMPLER-DUPLICATE-JOB-MONITOR-2026-07-22.md
task: TODO-S13-MEDIUM-FINE-SAMPLER-DUPLICATE-JOB-MONITOR-2026-07-22
date: 2026-07-22
role: Scheduler/cfd-pp/Reviewer/Writer
type: work_product
status: complete
---

# S13 Medium/Fine Sampler Duplicate-Job Monitor

Decision: `duplicate_jobs_completed_no_cancellation_needed_sampler_fail_closed_no_terminal_qoi_rows`.

Slurm jobs `3310176` and `3310179` both reached `COMPLETED` with exit code
`0:0`. No cancellation was needed by the time the monitor ran because neither
job remained active. Both job stdout files report the same sampler decision:
`partial_or_failed_sampling_fail_closed`.

The current S13 sampler package is not usable for terminal QOI evidence:

- `mesh_level_geometry_summary.csv` has six released geometry rows.
- `medium_fine_terminal_window_reductions.csv` is header-only.
- `medium_fine_exact_label_qoi_rows.csv` is header-only.
- `sampling_error_log.csv` has six errors, one for each case/mesh.

The deterministic repair is to add face area vector components to the generated
exchange-interface rows before calling `interface_reduction`. A rerun should use
a clean output package or a job lock so two Slurm jobs cannot write the same
directory.

No native output, registry, admission state, production harvest, source/property
release, Qwall release, coefficient admission, final score, or S11/S12/S13/S15/S6
trigger changed.
