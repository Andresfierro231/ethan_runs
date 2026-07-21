---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/physics_requirement_matrix.csv
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/next_model_contract.csv
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/README.md
tags: [forward-model, wall-fluid-coupling, test-section, dry-contract]
related:
  - .agent/status/2026-07-18_AGENT-541.md
  - imports/2026-07-18_tswfc2_dry_contract.json
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_dry_contract/README.md
task: AGENT-541
date: 2026-07-18
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# TSWFC2 Dry Contract

Task: AGENT-541

## Attempted

Implemented the next non-overlapping research-progress slice after AGENT-539:
a no-solver dry contract for `TSWFC2`, the distributed test-section wall/fluid
node model. This avoided the active AGENT-540 Fluid UMX1 implementation scope.

## Observed

AGENT-536 reports `decision=contract_first_no_grid`, zero admitted candidate
families, and `TSWFC2_distributed_test_section_wall_fluid_nodes` as the
secondary model after UMX1. Its requirement R2 says the next wall/fluid model
must use distributed wall/fluid nodes and must not duplicate AGENT-526.

AGENT-526 completed the one-node test-section bulk-to-ambient series-resistance
fallback, but both candidates failed validation and holdout mdot/TP/TW/all-probe
gates. AGENT-531 shows persistent scoreable TW5/TW6 and heated-incline
role-segment failures across passive distribution, wall-temperature drive, and
wall-circuit families.

AGENT-538 requires source-envelope and property-mode labels on future
scorecards before fit or admission rows are reported.

## Inferred

TSWFC2 is a plausible secondary path only if it changes topology and evidence
accounting: multiple axial nodes, separate fluid/inner-wall/outer-wall/external
states, a per-node conservation ledger, and frozen sensor/source-property
metadata. A single bulk-to-ambient replacement or mdot-only scorecard would
repeat the failed pattern.

## Contradictions And Caveats

This package does not implement Fluid interfaces and does not authorize a
scoring grid. AGENT-540 still owns the active UMX1 Fluid API path, so TSWFC2
implementation should wait until UMX1 is implemented, rejected, or blocked with
a clear handoff.

Salt1 role-row availability remains a hard gate. Missing Salt1 rows cannot be
silently omitted from fit-selection scoring under the current final predictive
split policy.

## Next Useful Actions

First inspect the completed AGENT-540 result. If UMX1 is unavailable or fails
cleanly, open a separate Fluid design row for TSWFC2 node interfaces. That row
should implement no-op/default behavior and dry output schemas before any smoke
or scoring run. Any future smoke run needs a separate scheduler-authorized row
and should run one or two predeclared cases only.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
external Fluid files, generated docs index files, reports/thesis files, active
two-tap sampler paths, fitting, tuning, model selection, or scientific admission
state were mutated.
