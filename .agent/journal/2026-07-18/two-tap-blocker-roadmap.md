---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/launch_readiness_gate.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/target_feature_taps.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/summary.json
tags: [pressure-ledger, two-tap, raw-endpoints, blockers, component-k, f6]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-BLOCKER-ROADMAP.md
  - imports/2026-07-18_two_tap_blocker_roadmap.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-BLOCKER-ROADMAP
date: 2026-07-18
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
---
# Two-Tap Blocker Roadmap

## Attempted

Implemented the plan requested after `TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS`:
identify blockers, research paths, and next steps forward from the completed
raw endpoint contract.

## Observed

The raw endpoint contract already resolved the target labels and time windows:
Salt2/Salt3/Salt4 `corner_lower_right`, upstream `lower_leg__s04`, downstream
`right_leg__s00`, time windows `7915/7618/10000`. It did not sample any raw
fields and did not change scientific admission.

The active blockers are pressure/velocity basis, straight-reference/component
isolation, recirculation metrics, and same-QOI UQ. Task scope and F6 separation
are governance gates; target taps are resolved but must be preserved exactly.

## Inferred

The next useful work is a separate staged-copy cfd-pp sampler. It must produce
finite endpoint `p`, `p_rgh`, `U`, `T_or_rho`, flux, area, normal, density/bulk
velocity reductions, and RAF/RMF/SVF before any extractor can be rebuilt.

The straight-reference path is likely still a blocker after raw sampling unless
component isolation can be made nonnegative without clipping. If not, the row
should remain apparent/cluster diagnostic.

## Contradictions Or Caveats

This line attacks the context around `f6-friction-re-correction`, but it is not
an F6 fitting lane. F6 needs separate ordinary nonrecirculating pressure anchors.

The staged raw-pressure precedent sampled a different feature
(`left_lower_leg__s00` to `left_upper_leg__s04`). That precedent must not be
substituted for `corner_lower_right`.

## Next Useful Actions

1. Claim a staged-copy cfd-pp row with task-owned `tmp/`/`work_products/` output.
2. Sample the exact endpoint surfaces from the raw endpoint plan.
3. Audit pressure/velocity basis and straight-reference/component isolation.
4. Compute same-window RAF/RMF/SVF.
5. Attach same-QOI UQ or explicit diagnostic-only status.
6. Build a new extractor/admission review without overwriting AGENT-530.
