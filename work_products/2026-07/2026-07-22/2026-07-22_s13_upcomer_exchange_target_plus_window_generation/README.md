---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/staged_case_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/dry_run_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/submission_manifest.csv
tags: [s13, upcomer-exchange, target-plus, openfoam, slurm]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-WINDOW-GENERATION-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/README.md
task: TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-WINDOW-GENERATION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer / Reviewer
type: work_product
status: active
---
# S13 Target-Plus Window Generation

Decision: `target_plus_windows_generated_ready_for_harvest_row`.

This package stages minimal restart clones for the nominal Salt2/Salt3/Salt4
S13 source cases and prepares Slurm jobs to generate the missing target-plus
windows needed before same-QOI neighbor-window UQ can be rerun.

- Salt2 target-plus: `7916`
- Salt3 target-plus: `7619`
- Salt4 target-plus: `10001`
- staged cases: `3`
- dry-run passed cases: `3`
- submitted jobs: Salt2 `3310047`, Salt3 `3310046`, Salt4 `3310048`
- terminal-success jobs: `3`
- target-plus directories present: `3`

The native source cases are read-only provenance. Only the staged clones under
`staging/s13_target_plus_window_generation_2026-07-22` may be advanced.

Do not run S13 harvest, same-QOI UQ, mesh/GCI UQ, or admission from this
package. Jobs `3310047`, `3310046`, and `3310048` reached terminal success and
the required fields are present, so the next row should harvest target-plus QOI
values from staged outputs only.
