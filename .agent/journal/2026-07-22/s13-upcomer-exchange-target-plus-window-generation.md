---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/staged_case_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/submission_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/job_terminal_status.csv
tags: [s13, upcomer-exchange, target-plus, openfoam, slurm]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-WINDOW-GENERATION-2026-07-22.md
  - imports/2026-07-22_s13_upcomer_exchange_target_plus_window_generation.json
task: TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-WINDOW-GENERATION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Target-Plus Window Generation

## Attempted

Implemented the target-plus generation path for nominal Salt2/Salt3/Salt4. The
work staged minimal local clones from native source cases, patched staged
runtime controls, dry-ran the OpenFOAM launcher, and submitted Slurm jobs from
`login3`.

## Observed

Direct `sbatch` from the current shell returned the TACC compute-node notice and
did not submit jobs. The first remote submission reached `login3` but failed
because the account was ambiguous. Existing NuclearEnergy jobs used account
`asc23046`, so the task-owned sbatch scripts were patched with
`#SBATCH --account=ASC23046` and resubmitted from `login3`.

Submitted jobs:

- Salt2 `s13_s2_tplus`: job `3310047`, `COMPLETED`, `0:0`, elapsed `00:02:53`.
- Salt3 `s13_s3_tplus`: job `3310046`, `COMPLETED`, `0:0`, elapsed `00:03:02`.
- Salt4 `s13_s4_tplus`: job `3310048`, `COMPLETED`, `0:0`, elapsed `00:03:17`.

The expected staged target-plus directories now exist:
Salt2 `7916`, Salt3 `7619`, and Salt4 `10001`.

## Inferred

The availability blocker is no longer the absence of target-plus field
directories. The next scientific blocker is whether target-plus QOI values can
be harvested with the exact same labels, formulas, sign conventions, and
geometry basis as the existing target-minus/target rows.

## Caveats

This row did not harvest QOIs, execute UQ, run production harvest, admit a
coefficient, mutate native source cases, edit registry/admission state, or edit
thesis current files. The generated target-plus windows are staged continuation
outputs, not native source outputs.

## Next Useful Actions

Claim a separate target-plus same-QOI harvest row. It should read only the
staged target-plus windows, produce the `12` target-plus QOI rows, join them to
the existing target-minus/target evidence, and then decide whether same-QOI
neighbor-window UQ can finally run.
