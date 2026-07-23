---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/physical_time_equivalence_proof.csv
tags: [journal, s13, same-physical-window, scheduler, mesh-gci, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-TRUE-SAME-PHYSICAL-WINDOW-MF-ROWS-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/README.md
task: TODO-S13-TRUE-SAME-PHYSICAL-WINDOW-MF-ROWS-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Scheduler / Implementer / Tester / Writer / Reviewer / Coordinator
type: journal
status: complete
---
# TODO-S13-TRUE-SAME-PHYSICAL-WINDOW-MF-ROWS-2026-07-22

## Attempted

Added the scheduler decision note requested by the user, verified Slurm partition spelling with `sinfo`, and built a task-owned recovery package to scan native medium/fine roots for exact coarse target-minus/target/target-plus physical labels.

Submitted the package through `login3` using `#SBATCH -p NuclearEnergy-dev` and `#SBATCH -A ASC23046`.

## Observed

Slurm job `3312178` completed on `NuclearEnergy-dev`. The native medium/fine roots exist for Salt2/Salt3/Salt4 medium/fine, but their processor time labels are terminal campaign labels such as Salt2 medium `515/516/517/518`, Salt2 fine `396/397/398/399`, Salt3 medium `1337/1338/1339/1340`, Salt3 fine `530/531/532/533`, Salt4 medium `1156/1157/1158/1159`, and Salt4 fine `414/415/416/417`. They do not contain the coarse target labels such as Salt2 `7914/7915/7916`, Salt3 `7617/7618/7619`, or Salt4 `9999/10000/10001`.

## Inferred

The repository now has an auditable no-go proof for true same-physical medium/fine extraction from the current native evidence. Role-equivalent terminal rows are useful diagnostics, but they cannot be used as formal same-physical-window rows.

Endpoint geometry is no longer the active S13 blocker. The active blocker is absence of medium/fine native output at the coarse physical labels.

## Caveats

No native field directories were created, no solver/reconstruction/postprocessing was launched, and no terminal proxy substitution was used. True row count is zero because exact native target directories are absent, not because endpoint geometry is missing.

## Next Useful Actions

Generate or reconstruct medium/fine native output at the coarse target-minus/target/target-plus labels, then run the true same-physical-window field sampler. Once true rows exist, rerun this package and then formal GCI/same-QOI UQ.
