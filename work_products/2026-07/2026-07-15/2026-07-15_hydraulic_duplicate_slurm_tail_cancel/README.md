---
provenance:
  - .agent/status/2026-07-15_AGENT-405.md
  - .agent/journal/2026-07-15/sensor-policy-gate-opening-and-hydraulic-node-run.md
  - work_products/2026-07/2026-07-14/2026-07-14_hydraulic_overnight_dependent_chain/slurm_dependency_tail_manifest.csv
tags: [scheduler, hydraulics, cleanup, duplicate-job-cancel]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run/README.md
task: AGENT-412
date: 2026-07-15
role: Coordinator/Hydraulics/Scheduler/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Hydraulic Duplicate Slurm Tail Cancel

## Decision

The dependency-held Slurm jobs `3295989`, `3295990`, and `3295991` were cancelled because their safe diagnostic equivalents had already been run locally on `c318-008` by AGENT-405.

## Before Cancel

All three jobs were pending in `NuclearEnergy-dev` with reason `Dependency`, elapsed time `0:00`, and no node assigned. They had not run.

## Action

Ran:

```bash
scancel 3295989 3295990 3295991
```

## After Cancel

`squeue` no longer lists the jobs. `sacct` reports all three as `CANCELLED by 890970`, elapsed `00:00:00`, with no node assigned.

## Replacement Evidence

AGENT-405 already produced the local node outputs:

- `test_section_complex_raw_two_tap_status.csv`: preflight only; not admitted.
- `f6_ready_to_run_gate.csv`: gate refresh; not admitted.
- `fluid_reset_k_diagnostic_sweep.csv`: 128 diagnostic rows; diagnostic component-separation evidence only.

## Guardrails

No native CFD outputs were modified. No OpenFOAM solver or postprocessing job was launched. No new Slurm jobs were submitted.
