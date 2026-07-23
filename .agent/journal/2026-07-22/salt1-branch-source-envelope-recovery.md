---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_salt1_train_external_bc_recovery_freeze_gate/salt1_external_bc_recovery_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict/salt1_recovered_operator_rows_for_fluid.csv
  - work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/salt1_branch_source_evidence_matrix.csv
tags: [salt1, source-envelope, source-property, passive-h2, predictive-1d]
related:
  - .agent/status/2026-07-22_TODO-SALT1-BRANCH-SOURCE-ENVELOPE-RECOVERY-2026-07-22.md
  - imports/2026-07-22_salt1_branch_source_envelope_recovery.json
  - operational_notes/07-26/22/2026-07-22_SALT1_BRANCH_SOURCE_ENVELOPE_RECOVERY.md
  - work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery/README.md
task: TODO-SALT1-BRANCH-SOURCE-ENVELOPE-RECOVERY-2026-07-22
date: 2026-07-22
role: Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Salt1 Branch Source-Envelope Recovery

## Attempted

Claimed a narrow unowned predictive-model blocker: Salt1 row-specific branch
source-envelope recovery. The purpose was to determine whether the completed
Salt1 external-boundary/runtime work could unlock source/property release for
Salt1-4 predictive freeze, or whether it should stay diagnostic.

## Observed

The previous Salt1 recovery package contains four Salt1 ambient-wall/operator
families: `cooling_branch`, `downcomer`, `lower_leg`, and `upcomer`. Those rows
have setup fields for `h`, `Ta`, `Tsur`, emissivity, wall-layer metadata, and
area values, and the later runtime package confirms the forbidden runtime flags
are false.

The fifth expected PASSIVE-H2 family, `junction`, is absent. The Salt1-4
postProcessing inventory does contain Salt1 junction wallHeatFlux diagnostic
rows; for example, the nominal Salt1 family has grouped junction wallHeatFlux
diagnostic context, but those rows are forbidden runtime inputs.

Every recovered non-junction Salt1 row still carries a wallHeatFlux or
postProcessing provenance trace through the source/area recovery path. That
makes the rows useful diagnostic evidence but not strict source-envelope release
evidence.

## Inferred

The Salt1 blocker has narrowed from "no runtime row" to two concrete release
requirements:

1. Recover a setup-only Salt1 `junction` operator row.
2. Replace wallHeatFlux-traced area/coverage provenance for the recovered
   non-junction families with setup-only mesh/geometry provenance.

Until both are done, Salt1 cannot support source/property release, a coefficient
freeze, or protected-row prediction scoring. The current four-row evidence can
still be used in the thesis as a diagnostic runtime-smoke result if the claim
boundary is explicit.

## Contradictions And Caveats

The earlier recovery package used language such as "setup schema or diagnostic
not fit candidate" and reported parser coverage passes. This package does not
overturn that diagnostic result. It applies the stricter final predictive
release standard and therefore keeps release closed.

The case metadata confirms Salt1 setup context and junction STL examples, but
it does not provide a mapped `junction` hA/operator row. The diagnostic
postProcessing junction wallHeatFlux rows show the missing family is physically
relevant but cannot be converted into a runtime coefficient without leakage.

## Next Useful Actions

1. Claim a setup-only Salt1 junction parser/recovery row. Done means a
   row-specific junction operator has segment mapping, area, h/Ta/Tsur,
   emissivity, wall-layer status, and no wallHeatFlux/postProcessing trace.
2. Claim a Salt1 area provenance repair row. Done means non-junction family
   areas and coverage are computed from mesh/geometry/setup fields or a
   documented invariant, not from realized wallHeatFlux.
3. Rerun candidate-specific S11/S15 source/property gates only after the above
   source-envelope blockers are cleared.
4. Keep Salt2 +/-5Q and `val_salt2` score-only until a frozen Salt1-4
   runtime-legal candidate exists.
