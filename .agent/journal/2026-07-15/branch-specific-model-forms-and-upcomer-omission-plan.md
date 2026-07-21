---
task: AGENT-435
date: 2026-07-15
role: Coordinator/Writer
type: journal
status: complete
tags: [branch-models, upcomer, recirculation, admission]
related:
  - operational_notes/07-26/15/2026-07-15_branch_specific_model_forms_and_upcomer_omission_plan.md
  - .agent/BOARD.md
---
# Branch-Specific Model Forms and Upcomer Omission Plan

## Observed Facts

- Current Salt2-4 upcomer evidence is recirculating.
- Existing policy already rejects single-stream `Nu`, `f_D`, and `K` labels in
  recirculating rows.
- The user clarified the intended next analysis: omit the recirculating upcomer
  branch from ordinary-pipe coefficient analysis and proceed on other branches,
  using different model forms per branch.

## Actions

- Added board TODO `TODO-BRANCH-SPECIFIC-ORDINARY-PIPE-SCORECARD`.
- Wrote
  `operational_notes/07-26/15/2026-07-15_branch_specific_model_forms_and_upcomer_omission_plan.md`.
- Updated forward-model and thermal/internal-Nu maps with the branch-specific
  policy.
- Updated the presentation outline with the advisor-facing phrasing:
  recirculating upcomer rows are omitted from ordinary-pipe coefficient fits;
  other branches proceed with branch-specific forms.

## Interpretation

This keeps the scientific result intact: the upcomer is not being ignored, but
it is excluded from the wrong model family. The branch-specific scorecard can
advance downcomer, heater/lower-leg, cooler/HX, test-section, and
junction/connector modeling while the upcomer remains in a separate
recirculation/hybrid/onset lane.

## Recommended Next Action

Claim `TODO-BRANCH-SPECIFIC-ORDINARY-PIPE-SCORECARD` before any ordinary
`Nu`, `f_D`, or `K` scorecard refresh, and publish the included/excluded branch
mask before reporting any aggregate fit score.
