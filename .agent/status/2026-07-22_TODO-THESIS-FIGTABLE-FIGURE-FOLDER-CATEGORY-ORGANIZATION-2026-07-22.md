---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/README.md
tags: [thesis, figures, organization, tp-vs-elevation, tp-tw-vs-elevation, progress]
related:
  - .agent/journal/2026-07-22/thesis-figtable-figure-folder-category-organization.md
  - imports/2026-07-22_thesis_figtable_figure_folder_category_organization.json
task: TODO-THESIS-FIGTABLE-FIGURE-FOLDER-CATEGORY-ORGANIZATION-2026-07-22
date: 2026-07-22
role: Figures / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status

## Objective

Organize the thesis figure package by category before figure type, with progress
figures separated from TP-only and combined TP/TW elevation figures.

## Changes Made

- Changed figure output layout from flat `figures/{svg,png}` to
  `figures/<category>/{svg,png}`.
- Wrote model-form ladder and blocked scorecard waterfall to
  `figures/progress/{svg,png}`.
- Restored regenerated TP-only elevation panels and wrote them to
  `figures/tp_vs_elevation/{svg,png}`.
- Wrote combined TP/TW elevation panels to
  `figures/tp_tw_vs_elevation/{svg,png}`.
- Wrote signed-error diagnostic panel to `figures/diagnostics/{svg,png}`.
- Added targeted cleanup for known stale flat figure files from the same package.
- Updated caption ledger paths, README output inventory, summary category counts,
  and regression tests.

## Validation

- `python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
  passed.
- Verified output tree has:
  - `progress`: 2 figure panels.
  - `tp_vs_elevation`: 3 figure panels.
  - `tp_tw_vs_elevation`: 3 figure panels.
  - `diagnostics`: 1 figure panel.
  - legacy flat figure paths retained: `0`.
- Visual spot-check: Salt2 TP-only PNG rendered from
  `figures/tp_vs_elevation/png/m3_tp_temperature_vs_elevation_salt_2.png`.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler, solver, sampler, harvest, or UQ launched: no.
- Fluid source or external repo edited: no.
- Thesis current/LaTeX files edited: no.
- Validation/holdout/external-test new scoring performed: no.
- Fitting, tuning, model selection, source/property release, coefficient
  admission, or final score claim made: no.
- S11/S12/S13/S15/S6 trigger changed: no.
- Blocker register changed before closeout: no.

## Remaining Caveats

This is an artifact-organization and figure-regeneration task only. Scientific
claims, target values, reference elevation basis, M3 predictions, and admission
status are unchanged.
