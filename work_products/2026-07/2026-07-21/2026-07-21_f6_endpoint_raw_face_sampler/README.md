---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_face_uq_execution/endpoint_face_sampling_matrix.csv
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight/raw_endpoint_sampling_contract.csv
tags: [f6, pressure-ledger, endpoint-sampler, raw-face]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_face_uq_execution/README.md
task: TODO-F6-ENDPOINT-RAW-FACE-SAMPLER
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# F6 Endpoint Raw Face Sampler

## Result

This package unblocks the F6 raw-face sampler path up to a scheduler-ready
Stage A handoff. It does not submit a job, mutate native solver output, fit F6,
or admit a component K.

Stage A contains `8` endpoint-face rows
from Salt2 medium/fine meshes. Coarse Salt2/Salt3/Salt4 rows remain blocked
until source-path repair proves required fields at retained times.

## Open First

1. `sampler_preflight_repair.csv`
2. `stage_a_endpoint_face_matrix.csv`
3. `raw_f6_endpoint_face_metrics.csv`
4. `scripts/run_stage_a_f6_endpoint_sampler.sh`

## How To Advance

Claim a separate scheduler-authorized row before launching. The future command
is:

```bash
sbatch work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/submit_stage_a_f6_endpoint_sampler.sbatch
```

After the job lands, rerun:

```bash
python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/build_f6_endpoint_raw_face_sampler.py --harvest --record-job-id <jobid>
```

## Guardrails

Raw face samples are diagnostic only. F6 fit and component-K admission remain
closed until raw RAF/RMF, same-QOI time UQ, accepted mesh/GCI or explicit
uncertainty bound, and F3 comparison pass in a separate admission-review row.
