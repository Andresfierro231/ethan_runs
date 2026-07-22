---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit/dominant_component_patch_overlap.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit/wall_candidate_component_review.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit/geometry_seed_requirements.csv
tags: [journal, s13, upcomer-exchange, roi, patch-alignment, no-admission]
related:
  - .agent/status/2026-07-21_TODO-S13-RIGHT-LEG-ROI-PATCH-ALIGNMENT-AUDIT-2026-07-21.md
  - imports/2026-07-21_s13_right_leg_roi_patch_alignment_audit.json
task: TODO-S13-RIGHT-LEG-ROI-PATCH-ALIGNMENT-AUDIT-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# S13 Right-Leg ROI Patch Alignment Audit

## Attempted

Audited the current reverse-flow ROI against trusted right-leg wall patch
evidence from the completed topology forensics, source-bounded CV package, and
geometry contract. No new mask was admitted.

## Observed

The dominant reverse-flow components for Salt2/Salt3/Salt4 all contact lower
leg patches and have zero trusted right-leg wall patch contact. Conservative
wall-contact components are absent or too small to release. Salt3 and Salt4
have tiny wall-adjacent candidates, but they touch the unreleased
`ncc_pipeleg_right_03_upper_end` boundary.

## Inferred

The current cell-center reverse-flow ROI is not describing the same physical
region as the trusted right-leg wall patch set. A direct patch-aware
segmentation should not be launched from this ROI without first declaring a
geometry-backed right-leg/upcomer seed.

## Contradictions Or Caveats

The result does not prove there is no recirculation exchange structure in the
right leg. It proves only that the current dominant velocity-mask rule is
misaligned with trusted wall geometry and cannot be promoted.

## Next Useful Actions

1. Define a predeclared geometry-backed right-leg/upcomer seed using trusted
   wall patches and conservative spatial limits.
2. Apply velocity/exchange tests inside that seeded geometry only after the
   seed is documented.
3. Rerun source-bounded CV release only if the seed produces positive trusted
   wall contact, positive exchange interface, and no untrusted boundary escape.
