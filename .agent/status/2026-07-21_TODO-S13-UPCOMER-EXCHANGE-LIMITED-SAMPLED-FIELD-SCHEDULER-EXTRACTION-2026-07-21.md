---
provenance:
  - tools/extract/build_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction.py
  - tools/extract/test_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/sampled_field_summary.csv
tags: [status, s13, upcomer-exchange, limited-sampled-field, scheduler, nonharvest]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-limited-sampled-field-scheduler-extraction.md
  - imports/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/README.md
task: TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-SCHEDULER-EXTRACTION-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer
type: status
status: complete
---
# TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-SCHEDULER-EXTRACTION-2026-07-21

## Objective

Run the limited scheduler-authorized sampled-field extraction for Salt2/Salt3
and Salt4 interface `U/T/rho` plus wall/core `T` from existing whole-mesh cell
VTK fields and released seeded geometry.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/`.

Slurm/accounting observed:

- `3308952` `s13_limsamp`: `CANCELLED+`, exit `0:0`, elapsed `00:00:00`,
  no node assigned; this submitted batch path did not execute the extraction.
- `3307325.0` `python3.11`: `COMPLETED`, exit `0:0`, elapsed `00:01:43`, node
  `c318-008`.
- Parent allocation/job `3307325` was still `RUNNING` when checked; this task
  did not cancel, requeue, or otherwise mutate that parent allocation.

Published extraction results:

- sampled summary rows: `3`
- sampled interface field rows: `116640`
- sampled wall/core temperature rows: `116640`
- `Q_wall_W` released rows: `0`
- sampler-ready rows: `0`
- production harvest allowed rows: `0`
- same-QOI UQ ready rows: `0`
- admission allowed rows: `0`

The decision is `limited_sampled_field_extraction_complete_nonharvest`.
Interface `U/T/rho` and trusted wall-owner `T` are now durable diagnostic inputs,
but wall temperature is not wallHeatFlux and does not release `Q_wall_W`.

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction.py`.
- Added `tools/extract/test_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction.py`.
- Generated the task sbatch wrapper plus sampled summary, sampled interface,
  sampled wall/core temperature, scheduler execution record, downstream gate,
  guardrail, source manifest, README, and summary artifacts.
- Added this status file, journal entry, and import manifest.

## Validation

- `squeue -j 3307325`: parent job `3307325` observed `RUNNING` on `c318-008`;
  no scheduler mutation performed.
- `sacct -j 3307325 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList,Submit,Start,End`:
  `3307325.0` observed `COMPLETED 0:0` in `00:01:43`.
- `sacct -j 3308952 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList,Submit,Start,End`:
  `3308952` observed `CANCELLED+ 0:0` with no node assigned.
- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction.py tools/extract/test_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction`:
  passed, `4` tests.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction --strict`:
  passed, `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-SCHEDULER-EXTRACTION-2026-07-21`:
  passed.
- `python3.11 tools/docs/build_repo_index.py --check`:
  passed, `blocker register OK (15 entries)`.

## Unresolved Blockers

Production S13 remains blocked. Missing inputs are still `Q_wall_W` or
wallHeatFlux-derived wall heat integration, pressure basis, viscosity basis,
`cp`, exact production QOI harvest, and same-QOI UQ.

## Guardrails

No native-output mutation, registry/admission mutation, OpenFOAM
solver/postprocessing launch, sampler/harvest launch, Fluid/external edit,
validation/holdout/external-test scoring, fitting/model selection,
source/property release, coefficient admission, `Q_wall_W` release,
sampler-ready promotion, production harvest, same-QOI UQ, S11/S12/S13/S15/S6
trigger, blocker-register change, generated-index refresh, thesis edit, or
residual absorption into internal `Nu`.
