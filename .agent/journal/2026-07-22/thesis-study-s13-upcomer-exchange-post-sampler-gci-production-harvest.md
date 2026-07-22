---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_duplicate_job_monitor/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_s13_upcomer_exchange_post_sampler_gci_production_harvest/summary.json
tags: [journal, s13, upcomer-exchange, post-sampler, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-POST-SAMPLER-GCI-PRODUCTION-HARVEST-2026-07-22.md
  - imports/2026-07-22_thesis_study_s13_upcomer_exchange_post_sampler_gci_production_harvest.json
task: TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-POST-SAMPLER-GCI-PRODUCTION-HARVEST-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Post-Sampler GCI / Production-Harvest Closeout

## Attempted

Closed the trigger-gated S13 post-sampler production-harvest row using existing
evidence only. The analysis consumed the completed medium/fine sampler package,
the duplicate-job monitor, the same-QOI temporal UQ package, the pre-sampler
mesh/GCI gate, and the earlier production-harvest fail-closed package.

## Observed

The medium/fine sampler completed at the Slurm level but not at the scientific
QOI level. It emitted `6` geometry rows, `0` terminal-window reductions, `0`
exact-label QOI rows, and `6` sampling errors. The four S13 QOI labels have
same-QOI temporal UQ from the target-minus/target/target-plus path, but all four
still lack post-sampler same-label medium/fine QOI rows.

## Inferred

The post-sampler trigger has fired, but it closes the gate negatively. Geometry
release is sufficient to guide a repair rerun; it is not sufficient to claim
mesh/GCI, production harvest, Qwall release, source/property release, an
exchange-cell coefficient, ordinary upcomer `Nu/f_D/K`, S11 review, S15 freeze,
or S6 scoring.

## Contradictions / Caveats

The scheduler reports normal job completion, while the package-level scientific
decision is fail-closed. This is not contradictory: the Slurm job executed and
reported a deterministic sampler error. The duplicate-run history also means a
future repair should write to a clean output package or enforce a job lock.

## Results

Published
`work_products/2026-07/2026-07-22/2026-07-22_thesis_study_s13_upcomer_exchange_post_sampler_gci_production_harvest/`
with:

- post-sampler artifact disposition
- four-QOI readiness table
- production go/no-go gate
- downstream S11/S15 consequence table
- repair queue
- figure/table targets
- source manifest and no-mutation guardrails

## Next Useful Actions

Patch the sampler face-area-vector contract first. Then run a unit test and a
single case/window smoke into a clean output directory. Only if that produces
finite exact-label QOI rows should a later row rerun the full six-case
medium/fine sampler and then recompute same-label mesh/GCI.
