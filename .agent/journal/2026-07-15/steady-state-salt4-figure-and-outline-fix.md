---
task: AGENT-434
date: 2026-07-15
role: Implementer/Tester/Writer
type: journal
status: complete
tags: [presentation-figures, steady-state, salt4]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig07_steady_state_rms_sem.svg
  - reports/thesis_dossier/2026-07-15_integrated_weekly_powerpoint_outline_definitions_first.md
---
# Steady-State Salt4 Figure and Outline Fix

## Observed facts

- `salt4_nominal` is present in
  `work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_user_train_scope/representative_metrics.csv`.
- Its representative final-window RMS values are TP `0.0512 K`, TW `0.0339 K`,
  and mdot `3.83e-05 kg/s`.
- The previous `fig07_steady_state_rms_sem.svg` selected Salt1, Salt1 Jin,
  Salt2 Jin, Salt3 Jin, and Salt2 validation, but omitted Salt4 nominal.

## Actions

- Added `salt4_nominal` to the selected cases in
  `tools/analyze/build_integrated_powerpoint_figures_and_definitions.py`.
- Regenerated `fig07_steady_state_rms_sem.svg`; it now labels Salt4 in both
  Max TP/TW RMS and mdot RMS panels.
- Updated the Slide 13 bullets in the Markdown outline with Salt4 nominal RMS
  values.
- Updated figure package metadata to `AGENT-434`.
- Added/updated tests so the generated figure must include Salt4.

## Validation

- `python3.11 tools/analyze/build_integrated_powerpoint_figures_and_definitions.py`
- `python3.11 -m pytest tools/analyze/test_integrated_powerpoint_figures_and_definitions.py`
- `rg` checks confirmed Salt4 label and values in the regenerated SVG and
  outline.

## Recommended next action

Use the updated `fig07` in the outline. The speaker note should explicitly say
Salt4 is included as a current training/reference row in this representative
steady-state check, while Salt2 val is diagnostic validation.
