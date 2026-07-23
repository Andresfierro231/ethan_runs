---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/direct_sampled_coarse_surface_field_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/formal_gci_rerun_disposition.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/same_qoi_uq_rerun_disposition.csv
tags: [status, s13, scheduler, coarse, mesh-gci, same-qoi-uq, fail-closed]
related:
  - .agent/journal/2026-07-22/s13-direct-coarse-extraction-gci-uq-chain.md
  - imports/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/README.md
task: TODO-S13-DIRECT-COARSE-EXTRACTION-GCI-UQ-CHAIN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Scheduler / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-DIRECT-COARSE-EXTRACTION-GCI-UQ-CHAIN-2026-07-22

## Objective

Execute the scheduler-authorized direct coarse extraction chain: generate direct sampled coarse surface-field rows from seeded coarse geometry using target-minus/target/target-plus native U, T, rho, and wallHeatFlux evidence; then resolve same-window medium/fine equivalence, endpoint residual basis, formal GCI disposition, and same-QOI UQ disposition.

## Outcome

Complete. Slurm job `3311815` ran on `c309-006.ls6.tacc.utexas.edu` and exited `COMPLETED 0:0` after `00:00:02`.

Decision: `direct_coarse_rows_generated_formal_gci_uq_blocked_by_equivalence_endpoint`.

Generated direct sampled coarse rows: `36`. Same-window equivalence admitted rows: `0/12`. Endpoint residual-basis ready rows: `0/6`. Formal GCI run rows: `0/4`. Formal same-QOI UQ rerun rows: `0/12`. Production harvest and admission rows remain `0`.

## Changes Made

- `tools/extract/build_s13_direct_coarse_extraction_gci_uq_chain.py`
- `tools/extract/test_s13_direct_coarse_extraction_gci_uq_chain.py`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/direct_sampled_coarse_surface_field_rows.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/coarse_case_qoi_neighbor_spread.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/same_window_medium_fine_equivalence_gate.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/endpoint_residual_basis_gate.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/formal_gci_rerun_disposition.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/same_qoi_uq_rerun_disposition.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/scheduler_execution_record.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/source_manifest.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/no_mutation_guardrails.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/summary.json`
- `.agent/status/2026-07-22_TODO-S13-DIRECT-COARSE-EXTRACTION-GCI-UQ-CHAIN-2026-07-22.md`
- `.agent/journal/2026-07-22/s13-direct-coarse-extraction-gci-uq-chain.md`
- `imports/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain.json`

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_direct_coarse_extraction_gci_uq_chain.py tools/extract/test_s13_direct_coarse_extraction_gci_uq_chain.py`
- `python3.11 tools/extract/build_s13_direct_coarse_extraction_gci_uq_chain.py`
- `ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/scripts/run_direct_coarse_extraction_chain.sbatch"`
- `ssh login3 "sacct -j 3311815 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList -P"`
- `python3.11 -m unittest tools.extract.test_s13_direct_coarse_extraction_gci_uq_chain`

## Blockers

Same-window medium/fine equivalence remains unresolved: the current medium/fine exact-label package does not admit the same physical target-minus/target/target-plus windows as the coarse chain.

Endpoint residual basis remains unresolved: endpoint candidate masks lack area vectors, owner cells, normals, and positive mdot sign convention, so pressure and energy endpoint residuals cannot be admitted.

## Guardrails

No native solver outputs, registry/admission state, Fluid/external repos, thesis files, source/property/Qwall releases, production harvests, formal GCI admissions, same-QOI UQ admissions, coefficients, protected scores, final scores, candidate freezes, deletions, commits, or pushes were mutated.
