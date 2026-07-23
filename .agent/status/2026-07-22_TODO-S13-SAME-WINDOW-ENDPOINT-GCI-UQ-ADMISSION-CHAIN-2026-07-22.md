---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/medium_fine_same_window_mapping_attempt.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/endpoint_residual_basis_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/formal_gci_rerun_disposition.csv
tags: [status, s13, same-window, endpoint-geometry, scheduler, mesh-gci, same-qoi-uq, fail-closed]
related:
  - .agent/journal/2026-07-22/s13-same-window-endpoint-gci-uq-admission-chain.md
  - imports/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/README.md
task: TODO-S13-SAME-WINDOW-ENDPOINT-GCI-UQ-ADMISSION-CHAIN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Scheduler / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-SAME-WINDOW-ENDPOINT-GCI-UQ-ADMISSION-CHAIN-2026-07-22

## Objective

Continue the S13 exchange-cell admission sequence: regenerate or map medium/fine rows onto the same physical coarse target-minus/target/target-plus windows, enrich endpoint inlet/outlet masks with face area vectors, owner cells, normals, and positive mdot convention, and only then rerun formal GCI and same-QOI UQ.

## Outcome

Complete with one blocker removed and one gate still fail-closed.

Slurm job `3312020` charged to `ASC23046`, ran on `c302-006`, and completed `0:0` in `00:00:11`. A first submit attempt without `-A ASC23046` failed before job creation because Slurm required an allocation choice.

Decision: `endpoint_basis_resolved_formal_gci_uq_blocked_by_same_window_equivalence`.

Endpoint geometry enrichment succeeded: `288` endpoint face rows and `6/6` released endpoint masks now include `area_m2`, `area_vector_x/y/z_m2`, `owner_cell`, normal convention, positive mdot convention, `time_window_s`, and source polyMesh provenance.

Same-window mapping remains closed: `72` mapping-attempt rows were written, but medium/fine native processor directories do not contain the coarse physical target-minus/target/target-plus time labels, so same-window equivalence admitted `0/12` rows. Role-equivalent terminal rows were recorded as proxy-only and not admitted.

Formal GCI and same-QOI UQ were not run: formal GCI run rows `0/4`, same-QOI UQ rerun rows `0/12`, production harvest/admission rows `0`.

## Changes Made

- `tools/extract/build_s13_same_window_endpoint_gci_uq_admission_chain.py`
- `tools/extract/test_s13_same_window_endpoint_gci_uq_admission_chain.py`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/medium_fine_same_window_mapping_attempt.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/same_window_medium_fine_equivalence_gate.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/endpoint_geometry_enriched_face_rows.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/endpoint_residual_basis_gate.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/released_endpoint_masks/*.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/formal_gci_rerun_disposition.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/same_qoi_uq_rerun_disposition.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/scheduler_execution_record.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/source_manifest.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/no_mutation_guardrails.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/summary.json`
- `.agent/status/2026-07-22_TODO-S13-SAME-WINDOW-ENDPOINT-GCI-UQ-ADMISSION-CHAIN-2026-07-22.md`
- `.agent/journal/2026-07-22/s13-same-window-endpoint-gci-uq-admission-chain.md`
- `imports/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain.json`

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_same_window_endpoint_gci_uq_admission_chain.py tools/extract/test_s13_same_window_endpoint_gci_uq_admission_chain.py`
- `python3.11 tools/extract/build_s13_same_window_endpoint_gci_uq_admission_chain.py`
- `ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/scripts/run_same_window_endpoint_gci_uq_chain.sbatch"`
- `ssh login3 "sacct -j 3312020 --format=JobID,Account,JobName,State,ExitCode,Elapsed,NodeList -P"`
- `python3.11 -m unittest tools.extract.test_s13_same_window_endpoint_gci_uq_admission_chain`

## Unresolved Blockers

Same-window medium/fine equivalence is still unresolved. The clean next action is to regenerate medium/fine samples at the coarse target-minus/target/target-plus physical labels, or produce a separate auditable physical-time equivalence proof. Current terminal role mapping is not enough.

## Guardrails

No native solver outputs, registry/admission state, Fluid/external repos, thesis files, source/property/Qwall releases, production harvests, formal GCI admissions, same-QOI UQ admissions, coefficients, protected scores, final scores, candidate freezes, deletions, commits, or pushes were mutated.
