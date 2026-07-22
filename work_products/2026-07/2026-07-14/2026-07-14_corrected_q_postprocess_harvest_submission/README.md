---
provenance:
  task: AGENT-342
  generated_by: codex
tags: [cfd-pp, salt-cfd, corrected-q, postprocessing, harvest]
related:
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/corrected_q_perturbation_status.csv
---
# Corrected-Q Salt2/Salt4 Postprocess Harvest Submission

## Purpose

Submit harvest jobs for Salt2/Salt4 corrected-Q perturbation rows without mutating native CFD solver outputs. Harvest means registry aggregation of existing `postProcessing`, corrected-Q status refresh, and read-only terminal monitor/gate evidence. Admission remains a separate decision.

## Submitted Drivers

- `run_salt2_salt4_stopped_corrected_q_harvest.sbatch`: immediate harvest for stopped Salt2/Salt4 +/-5Q rows.
- `run_salt2_salt4_selected_corrected_q_harvest_after_3293924.sbatch`: dependency-gated harvest for selected Salt2/Salt4 +/-10Q rows after Slurm job `3293924` exits.

## Salt1 Diagnostic Rationale

Salt1 is diagnostic because the documented corrected-Q stop was controlled by a weak global `convergenceMonitor`/early-stop path, and the current Salt1 policy still requires explicit admission plus operating-point movement and quasi-steady time-window UQ. The campaign README also states the policy correction: `too_short` alone is not an exclusion for a converged terminal row, but Salt1 still needs the Salt1-specific policy/gate before fit use.

## Outputs Expected After Jobs Run

- Registry aggregates under `registry/salt2/`, `registry/salt4/`, and global `_all_postprocessing_runs` indexes.
- Work-product logs and status tables under `stopped_salt2_salt4_pm5q/` and `selected_salt2_salt4_pm10q_after_3293924/`.
- Terminal monitor output for the selected +/-10Q rows after job `3293924` exits.

