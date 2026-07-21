---
task: AGENT-433
date: 2026-07-15
role: Implementer/Tester/Writer
type: journal
status: complete
tags: [presentation-figures, rmse, steady-state, svg]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig06_heater_cooler_rmse.svg
  - work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig07_steady_state_rms_sem.svg
  - reports/thesis_dossier/2026-07-15_integrated_weekly_powerpoint_outline_definitions_first.md
---
# Figure RMSE Context and Steady-State Label Fix

## Observed facts

- `fig06_heater_cooler_rmse.svg` showed power RMSE values but did not explain
  the reference quantity or modeling assumptions.
- The source table is
  `work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/heater_cooler_model_form_errors.csv`.
  Its RMSE values are power errors against CFD-realized component power:
  cooler removal for cooler rows and heater-to-fluid power for heater rows.
- `fig07_steady_state_rms_sem.svg` used long case labels and one-decimal
  small-axis tick labels, causing bottom text crowding and repeated-looking
  `0.1`/`0.2` tick labels.

## Actions

- Regenerated the integrated figure package from the builder script.
- Reworked `fig06_heater_cooler_rmse.svg` to state:
  - RMSE reference is CFD-realized cooler removal or heater-to-fluid power.
  - Rows are Salt2/3/4 nominal cases.
  - `Salt2-fit UA` means `Q_cool = UA DeltaT_bulk`, one scalar fit on Salt2
    and scored on Salt3/Salt4 without refit.
  - `Salt2-fit eta` means `Q_heater = eta P_electrical`, one scalar fit on
    Salt2 and scored on Salt3/Salt4 without refit.
  - These are model-form clues, not final admitted predictive results.
- Reworked `fig07_steady_state_rms_sem.svg` with short case labels, a case-label
  note, scale-aware axis tick formatting, and scale-aware value labels such as
  `0.024 K` rather than `0.0 K`.
- Updated the Markdown outline slide 11 with the same RMSE reference and
  Salt2-fit assumptions.
- Added focused tests for the new figure text and small-axis tick behavior.

## Validation

- `python3.11 tools/analyze/build_integrated_powerpoint_figures_and_definitions.py`
- `python3.11 -m pytest tools/analyze/test_integrated_powerpoint_figures_and_definitions.py`
- `rg` checks confirmed the expected phrases in the regenerated SVGs and
  outline.

## Recommended next action

Use the revised figure text directly in the presentation. For the spoken
narrative, say that `fig06` is a component-power closure score, not TP/TW RMSE,
and that the Salt2-fit rows are diagnostic one-scalar model-form candidates
pending validation/holdout admission.
