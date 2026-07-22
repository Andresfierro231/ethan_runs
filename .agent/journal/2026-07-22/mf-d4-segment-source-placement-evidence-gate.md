---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate/source_bounded_candidate_gate.csv
tags: [model-form, d4, segment-source-placement, source-bounded-gate, thesis]
related:
  - .agent/status/2026-07-22_TODO-MF-D4-SEGMENT-SOURCE-PLACEMENT-EVIDENCE-GATE-2026-07-22.md
  - imports/2026-07-22_mf_d4_segment_source_placement_evidence_gate.json
task: TODO-MF-D4-SEGMENT-SOURCE-PLACEMENT-EVIDENCE-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Tester / Writer / Reviewer
type: journal
status: complete
---
# Journal: D4 Segment Source-Placement Evidence Gate

## Attempted

Mapped D4 residual corrections by source segment and joined the four target
segments to independent setup/source/passive heat-path evidence.

## Observed

D4 improves every target segment tested:

- heated incline
- left lower vertical
- left upper vertical
- right vertical

The strongest raw segment improvement is `right_vertical`, but that maps to a
passive downcomer heat-path family with no released source/property or geometry
basis. The left vertical segments map to upcomer/test-section evidence, and
heated incline maps to lower-leg heater/passive evidence. Those evidence lanes
are useful but not release-ready.

## Inferred

D4 is a strong guide for where independent source placement should be pursued.
It is not a repair. The follow-on work should focus on released source/property
and geometry basis for downcomer/right-wall and upcomer/left-leg heat paths
before trying any runtime model change.

## Caveats

No new fit was run. Salt3/Salt4 are not used for tuning. The package only
crosswalks existing diagnostic residuals and existing source-basis packages.

## Next Useful Actions

1. Continue to the D3 wall-shape/axial-mixing gate.
2. Use the D4 segment map when claiming the passive wall/test-section
   source-bounded repair row.
3. Do not promote D4 coefficients into runtime inputs.
