---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling/sampling_command_contract.csv
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/RUNNING.md
tags: [s13, upcomer-exchange, medium-fine, sampler, journal]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-EXACT-LABEL-SAMPLER-2026-07-22.md
  - imports/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler.json
task: TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-EXACT-LABEL-SAMPLER-2026-07-22
date: 2026-07-22
role: Implementer/Tester/Writer/Scheduler
type: journal
status: complete
---
# S13 Medium/Fine Exact-Label Sampler

## Attempted

Activated the scheduler-authorized compute row for exact-label medium/fine S13
sampling. The reducer is task-scoped and reads the completed
`sampling_command_contract.csv`; it rebuilds mesh-level trusted-wall,
exchange-interface, recirculation-CV, wall/core/bulk masks from medium/fine
`constant/polyMesh`, then samples terminal candidate windows with the exact S13
labels.

## Observed

The lightweight tests pass against the current reducer interface. The Slurm
wrapper already invokes:

```bash
python3.11 tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py --execute --job-id "${SLURM_JOB_ID:-unknown}"
```

Direct `sbatch` from this shell reported that submission is unavailable from
compute nodes. Submission through `login3` succeeded and returned Slurm job
`3310179`. `squeue -j 3310179` showed the job running on `c318-019`; stdout and
stderr were still empty at the last check.

SSH to `c318-019` confirmed the active batch process:
`python3.11 tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py --execute --job-id 3310179`.
The job had written Salt2-medium mask/face contracts, so it had moved beyond
preflight into the mesh/field reduction path.

An accidental duplicate local `srun` wrapper in allocation step `3307325.2`
was killed after it was found targeting the same package path. This prevented a
non-batch duplicate from clobbering the Slurm job's eventual outputs. Job
`3310179` was left running.

## Inferred

The source-contract blocker is now unlocked into an active compute reduction.
The scientific gate is still closed: terminal medium/fine rows, if produced,
will require a later terminal-window equivalence review before mesh/GCI can be
rerun.

## Caveats

The job completed at the scheduler level but failed closed scientifically. The
final package reports `6` ready source-contract rows, `6` geometry rows, `0`
terminal-window reduction rows, `0` exact-label QOI rows, and `6` sampling
errors. Each Salt2/Salt3/Salt4 medium/fine case failed because the generated
face rows lacked the face area vector components required by the exact
interface/wall reductions.

Do not substitute endpoint/probe/profile/postProcessing proxy rows for the four
exact S13 labels.

## Next Useful Actions

1. Claim a narrow face-area-vector repair row.
2. Repair the medium/fine sampler so generated trusted-wall and
   exchange-interface face CSVs include face area vector components from
   `constant/polyMesh`.
3. Rerun exact-label sampling only after tests prove the vectors are present.
4. Only if exact-label rows exist, continue to terminal-window equivalence and
   mesh/GCI disposition in a separate row.
