---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/split_job_terminal_summary.csv
tags: [journal, s13, medium-fine, exact-label, split-rerun]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-EXACT-LABEL-SPLIT-RERUN-2026-07-22.md
  - imports/2026-07-22_s13_medium_fine_exact_label_split_rerun.json
task: TODO-S13-MEDIUM-FINE-EXACT-LABEL-SPLIT-RERUN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer
type: journal
status: complete
---
# S13 Medium/Fine Exact-Label Split Rerun

## Attempted

Ran the repaired medium/fine exact-label sampler as one Slurm array with six
unique case/mesh output directories after the Salt2/medium one-window smoke
passed.

## Observed

All six array elements completed with exit code `0:0`. Each child output has
three terminal-window reductions, twelve exact-label QOI rows, and zero
sampling errors. The aggregate has seventy-two QOI rows across four QOIs and
eighteen terminal-window reductions.

## Inferred

The face-area-vector blocker is resolved for the full Salt2/Salt3/Salt4
medium/fine matrix. The immediate next scientific gate is no longer extraction;
it is mesh/GCI disposition on the exact-label rows.

## Caveats

The child summaries still report
`terminal_exact_label_rows_sampled_mesh_gci_fail_closed_time_equivalence_missing`.
That is expected: this row only creates exact-label rows and an unlock gate. It
does not run GCI, admit production harvest, fit coefficients, or release source
property/Qwall evidence.

## Next Useful Actions

Open a separate mesh/GCI disposition row. If medium/fine behavior passes, it
should still remain diagnostic until same-window UQ and source/property/cp
validity are admitted for the same QOIs.
