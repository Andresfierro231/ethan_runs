---
provenance:
  - tools/extract/build_s13_right_leg_roi_patch_alignment_audit.py
  - tools/extract/test_s13_right_leg_roi_patch_alignment_audit.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit/roi_patch_alignment_decision.csv
tags: [s13, upcomer-exchange, roi, patch-alignment, geometry-seed, status]
related:
  - .agent/journal/2026-07-21/s13-right-leg-roi-patch-alignment-audit.md
  - imports/2026-07-21_s13_right_leg_roi_patch_alignment_audit.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/README.md
task: TODO-S13-RIGHT-LEG-ROI-PATCH-ALIGNMENT-AUDIT-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-S13-RIGHT-LEG-ROI-PATCH-ALIGNMENT-AUDIT-2026-07-21

## Objective

Audit whether the current reverse-flow cell-center ROI and trusted right-leg
wall patches describe the same physical S13 region, using completed topology
forensics and geometry-contract evidence only.

## Outcome

Complete as fail-closed. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit/`.

Key results:

- Decision: `complete_fail_closed_geometry_seed_required`.
- Dominant components aligned with trusted right-leg wall patches: `false`.
- Wall-candidate components released: `false`.
- New CV admitted: `false`.
- S12 unlocked: `false`.

Observed alignment:

- Salt2/Salt3/Salt4 dominant components all occupy `y=-0.256332248` to
  `-0.19609` and touch lower-leg patches:
  `ncc_pipeleg_lower_09_fitting_end`, `pipeleg_lower_06_straight`,
  `pipeleg_lower_07_bend`, `pipeleg_lower_08_straight`, and
  `pipeleg_lower_09_fitting`.
- Trusted right-leg wall patch contact count is `0` for the dominant component
  in all three cases.
- Wall-adjacent alternates are not releaseable: Salt2 has no trusted-contact
  component, Salt3 has `10` cells, and Salt4 has `84` cells; Salt3/Salt4 touch
  `ncc_pipeleg_right_03_upper_end`.

## Changes Made

- Validated and regenerated the ROI/patch-alignment audit package.
- Added this status file, journal entry, and import manifest.
- Board row still needs archive hygiene after finish validation; scientific
  status is complete.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_right_leg_roi_patch_alignment_audit.py tools/extract/test_s13_right_leg_roi_patch_alignment_audit.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_right_leg_roi_patch_alignment_audit`:
  passed, `4` tests.
- `python3.11 tools/extract/build_s13_right_leg_roi_patch_alignment_audit.py`:
  passed and regenerated the fail-closed package.

## Unresolved Blockers

- A direct patch-aware CV release is not justified from the current
  velocity-only dominant component rule.
- Next geometry work must define a predeclared geometry-backed
  right-leg/upcomer seed tied to `pipeleg_right_01_lower`,
  `pipeleg_right_02_middle`, and `pipeleg_right_03_upper`.
- S13 sampler/harvest/UQ, S12-HIAX1, and S11/S15/S6 triggers remain blocked.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/surface extraction/sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Threshold relaxation or new mask admission: no.
- Exchange-cell admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
