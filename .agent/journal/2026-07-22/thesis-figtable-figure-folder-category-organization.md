---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/figures
tags: [thesis, figures, organization, categories]
related:
  - .agent/status/2026-07-22_TODO-THESIS-FIGTABLE-FIGURE-FOLDER-CATEGORY-ORGANIZATION-2026-07-22.md
  - imports/2026-07-22_thesis_figtable_figure_folder_category_organization.json
task: TODO-THESIS-FIGTABLE-FIGURE-FOLDER-CATEGORY-ORGANIZATION-2026-07-22
date: 2026-07-22
role: Figures / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Journal

## Attempted

Reorganized the thesis model-form figure package so figure category appears
before file type, per the requested structure.

## Observed

The package had a flat `figures/svg` and `figures/png` layout containing
progress figures, signed-error diagnostics, combined TP/TW elevation figures,
and older TP-only elevation figures. The active builder generated only the
combined TP/TW, signed-error, ladder, and waterfall panels, leaving TP-only
figures as stale artifacts.

## Inferred

The reproducible fix is to make category part of the builder's save path and to
restore TP-only panel generation from the corrected TP/TW point table. Moving
files after generation would have left the next builder run able to recreate the
old flat layout.

## Changed

Added categorized save paths under `figures/progress`, `figures/tp_vs_elevation`,
`figures/tp_tw_vs_elevation`, and `figures/diagnostics`, each with `svg` and
`png` subfolders. Added a targeted cleanup for known flat generated figure
basenames. Added regenerated TP-only panels from the corrected experimental
target/reference-elevation data.

## Validation

The regression test passed and now asserts the new paths, category counts, nine
caption rows, 18 TP-only rows, and zero retained flat figure paths. The Salt2
TP-only panel was visually inspected.

## Next Useful Actions

Future figure work should use `save_figure(fig, category, basename)` and avoid
writing directly under `figures/svg` or `figures/png`.
