---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/probe_residual_atlas.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/role_segment_residual_atlas.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/invariant_failure_modes.csv
  - operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/coupled_delta_vs_m3.csv
tags: [forward-model, wall-test-section, tp-tw, failure-forensics]
related:
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/README.md
  - .agent/status/2026-07-18_AGENT-536.md
  - imports/2026-07-18_tp_tw_failure_forensics.json
task: AGENT-536
date: 2026-07-18
role: Implementer/Tester/Writer
type: journal
status: complete
---
# TP/TW Failure Forensics

## Attempted

Built an existing-evidence forensics package from AGENT-531 wall/test-section
blocker audit outputs and the AGENT-533 weekend handoff. Added the AGENT-526
single-node test-section wall/fluid fallback as a blocked candidate family,
because the handoff says it completed after the audit and must not be
duplicated unchanged.

## Observed

The sensor and role/segment ranks put heated-incline TW failures at the top of
the wall/test-section problem. Candidate families continue to improve mdot in
some rows while TP, TW, and all-probe errors worsen. AGENT-526 shows the same
pattern for the single-node wall/fluid series resistance.

## Inferred

The next requirement is an axial/branch thermal-shape mechanism, preferably an
energy-conserving upcomer exchange/stratification model. A distributed
test-section wall/fluid model remains plausible, but only as a second lane and
only if it is not the already-failed one-node bulk-to-ambient series model.

## Caveats

No new Fluid run was launched and no candidate was admitted. These matrices are
a pre-grid contract, not a replacement for coupled scorecards.

## Next Useful Actions

1. Audit Fluid for a real upcomer mixing/stratification/exchange hook.
2. Emit the UMX1 static API/scenario/root contract before any parameter grid.
3. Stop on missing hook, forbidden runtime input, Salt4 rejected root, or
   Salt3/blind leakage.

## Counts

Sensor rows: `15`. Role/segment rows:
`10`. Candidate family rows:
`10`. Physics requirement rows:
`5`. Next-model contract rows:
`4`.
