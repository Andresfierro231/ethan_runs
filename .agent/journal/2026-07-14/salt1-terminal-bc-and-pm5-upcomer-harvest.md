---
provenance:
  task: AGENT-363
  generated_by: codex
tags: [journal, cfd-pp, salt1, boundary-conditions, upcomer]
related:
  - .agent/status/2026-07-14_AGENT-363.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/README.md
---
# Salt1 Terminal BC And PM5 Upcomer Harvest

## Work Performed

Generated a patch-complete Salt1 terminal BC role table from the actual terminal
case dictionaries for:

- `salt1_jin_nominal_continuation_corrected`
- `salt1_jin_lo10q_corrected`
- `salt1_jin_hi10q_corrected`

Each row joins `0/T` thermal BC parameters with `constant/polyMesh/boundary`
mesh patch metadata. Roles separate heater/source, cooler/HX/removal, passive
`rcExternalTemperature`, passive `externalTemperature`, and zero-gradient
constraint/coupled patches.

## Salt1 hi10q Resolution

The previous conflict was an ordering problem between older inventory evidence
and later terminal harvest evidence. The older salt inventory marked hi10q as
failed/not-admissible from a stale latest-time gate. The terminal harvest
package records terminal stationary evidence for `4987-5587 s`, and the new BC
table proves the terminal case labels and Q mutations patch by patch.

Decision: `salt1_hi10q` is usable now as a training perturbation row. It must
remain labeled as hi10q and should not be collapsed into nominal Salt1.

## PM5 Pressure/Upcomer

Job `3295901` remains pending priority. There are no parsed matched-plane files
yet, so pressure/upcomer admission cannot be completed until the job runs.

Next monitor commands:

```bash
squeue -j 3295901
sacct -j 3295901 --format JobID,JobName,State,Elapsed,ExitCode -P
```

After terminal state, review the AGENT-357 logs and parsed CSVs.

## Validation

Focused builder and tests passed. Native CFD outputs were read-only.
