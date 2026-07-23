---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/physical_time_equivalence_proof.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/native_medium_fine_time_inventory.csv
tags: [status, s13, same-physical-window, scheduler, mesh-gci, same-qoi-uq, fail-closed]
related:
  - .agent/journal/2026-07-22/s13-true-same-physical-window-mf-rows.md
  - imports/2026-07-22_s13_true_same_physical_window_mf_rows.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/README.md
task: TODO-S13-TRUE-SAME-PHYSICAL-WINDOW-MF-ROWS-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Scheduler / Implementer / Tester / Writer / Reviewer / Coordinator
type: status
status: complete
---
# TODO-S13-TRUE-SAME-PHYSICAL-WINDOW-MF-ROWS-2026-07-22

## Objective

Record the scheduler rule to avoid `development`, then make the strongest possible S13 same-physical-window recovery attempt: scan native medium/fine roots for the coarse target-minus/target/target-plus labels, generate true rows only where exact native target directories exist, produce an auditable physical-time equivalence proof, and rerun formal GCI/UQ only if gates pass.

## Outcome

Complete. Added a durable scheduler decision: use the NuclearEnergy dev queue, spelled by Slurm as `NuclearEnergy-dev`, with account `ASC23046`; do not submit this workflow to `development`.

Slurm job `3312178` ran on `NuclearEnergy-dev`, account `ASC23046`, node `c318-008`, and completed `0:0` in `00:00:01`.

Decision: `true_same_physical_medium_fine_rows_blocked_exact_native_times_absent`.

The native medium/fine inventory found `6` case/mesh roots. None contains the coarse physical target labels in root or processor time directories. The scan produced `18` case/mesh/window rows, `0` exact native target rows, `0` true medium/fine same-physical rows, and `0/18` admitted physical-time equivalence rows. Endpoint residual basis remains ready at `6/6`. Formal GCI run rows remain `0/4`; same-QOI UQ rerun rows remain `0/12`.

## Changes Made

- `.agent/DECISIONS.md`
- `tools/extract/build_s13_true_same_physical_window_mf_rows.py`
- `tools/extract/test_s13_true_same_physical_window_mf_rows.py`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/native_medium_fine_time_inventory.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/same_physical_target_window_scan.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/true_medium_fine_same_physical_rows.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/physical_time_equivalence_proof.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/formal_gci_rerun_disposition.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/same_qoi_uq_rerun_disposition.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/scheduler_execution_record.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/source_manifest.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/no_mutation_guardrails.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/summary.json`
- `.agent/status/2026-07-22_TODO-S13-TRUE-SAME-PHYSICAL-WINDOW-MF-ROWS-2026-07-22.md`
- `.agent/journal/2026-07-22/s13-true-same-physical-window-mf-rows.md`
- `imports/2026-07-22_s13_true_same_physical_window_mf_rows.json`

## Validation

- `ssh login3 "sinfo -s | grep -E 'NuclearEnergy|PARTITION'"`
- `python3.11 -m py_compile tools/extract/build_s13_true_same_physical_window_mf_rows.py tools/extract/test_s13_true_same_physical_window_mf_rows.py`
- `python3.11 tools/extract/build_s13_true_same_physical_window_mf_rows.py`
- `ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-22/2026-07-22_s13_true_same_physical_window_mf_rows/scripts/run_true_same_physical_window_mf_rows.sbatch"`
- `ssh login3 "sacct -j 3312178 --format=JobID,Account,Partition,JobName,State,ExitCode,Elapsed,NodeList -P"`
- `python3.11 -m unittest tools.extract.test_s13_true_same_physical_window_mf_rows`

## Unresolved Blockers

True same-physical medium/fine rows do not exist in the current native evidence because the exact coarse target labels are absent from all six medium/fine roots. The clean unblock is new medium/fine native output generation or reconstruction at the coarse target-minus/target/target-plus labels, followed by a field sampler rerun.

## Guardrails

No native solver outputs, registry/admission state, Fluid/external repos, thesis files, source/property/Qwall releases, production harvests, formal GCI admissions, same-QOI UQ admissions, coefficients, protected scores, final scores, candidate freezes, deletions, commits, or pushes were mutated. The task used `NuclearEnergy-dev`, not `development`.
