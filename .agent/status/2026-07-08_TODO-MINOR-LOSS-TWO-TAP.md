# TODO-MINOR-LOSS-TWO-TAP Status

Date: `2026-07-08`
Role: Implementer / Tester
Owner: codex

## Scope

Build a read-only two-tap minor-loss reduction from existing Salt 2/3/4 Jin
pressure/minor-loss evidence. The output must separate diagnostic apparent `K`
from a corrected local `K` that subtracts adjacent distributed straight loss
where the available ledger supports it.

Editable paths:

- `.agent/BOARD.md` own row only
- `.agent/status/2026-07-08_TODO-MINOR-LOSS-TWO-TAP.md`
- `.agent/journal/2026-07-08/minor-loss-two-tap.md`
- `tools/extract/sample_minor_loss_two_tap.py`
- `tools/extract/test_sample_minor_loss_two_tap.py`
- `work_products/2026-07-08_minor_loss_two_tap/**`

## Completed

- Added `tools/extract/sample_minor_loss_two_tap.py`.
- Added `tools/extract/test_sample_minor_loss_two_tap.py`.
- Generated `work_products/2026-07-08_minor_loss_two_tap/**`.
- Emitted:
  - `minor_loss_two_tap.csv`
  - `minor_loss_two_tap.json`
  - `summary.json`
  - `README.md`

## Current State

Complete. The package is a conservative two-tap minor-loss ledger from preserved
feature endpoint evidence. It does not run new OpenFOAM extraction.

## Required Evidence Inputs

- `tools/extract/sample_bend_minor_loss.py`
- `tools/extract/sample_feature_minor_loss_budget.py`
- `tools/analyze/summarize_corner_pressure_drops.py`
- `operational_notes/06-26/25/2026-06-25_ethan_corner_pressure_drop_math.md`
- `work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.csv`

## Acceptance Targets

- Emit `minor_loss_two_tap.csv` and `.json`.
- Emit `K_local` and diagnostic `K_apparent`.
- Subtract adjacent straight distributed loss where possible.
- Mark rows that are recirculation-adjacent, upper-bound-only, or missing a
  proper two-tap total-pressure path.
- Join rows to the pressure ledger by case/span/feature.

All acceptance targets are met within the preserved-evidence limitation. The
preserved feature rows do not carry full centerline tap-to-tap length, so
`K_local` subtracts a minimum adjacent straight-loss estimate based on
`abs(dz_across_feature_m)` and remains an upper-bound estimate.

## Results

- `15` rows total: `3` Salt cases × `5` expected features.
- `12` computed preserved corner rows.
- `3` unavailable `test_section_complex` rows marked
  `feature_not_in_preserved_bend_minor_loss;requires_raw_two_tap_extraction`.
- `K_apparent` range: `6.2247` to `16.5038`.
- `K_local` range after minimum adjacent-straight-loss subtraction: `1.0661` to
  `8.7476`.
- Rows adjacent to `left_lower_leg` or `left_upper_leg` are flagged
  `recirculation_adjacent` and are validation diagnostics, not ordinary
  single-stream closure fits.

## Observed Facts

- The preserved July 1 bend-minor-loss package contains only four corner
  features per Salt 2/3/4 case.
- The expected `test_section_complex` connector/expansion-contraction feature is
  present in the case-analysis profile but absent from the preserved July 1 bend
  CSVs.
- The July 8 pressure ledger supplies adjacent distributed-loss gradients and
  recirculation flags needed for a stricter minor-loss table.

## Inferred Interpretation

- The legacy corner `K` values were apparent feature losses with no adjacent
  straight-loss subtraction.
- Subtracting even a minimum straight-loss proxy substantially lowers the corner
  `K` estimates, so previous bend `K` values should remain upper-bound
  diagnostics.
- A full closure-grade minor-loss result still requires raw two-tap extraction
  with centerline tap-to-tap length and reducer/connector rows.

## Blockers / Work In Progress

- Full centerline tap-to-tap feature lengths are not present in the preserved
  bend CSVs.
- Test-section connector/reducer feature rows need raw extraction.
- All rows remain `coarse_no_gci`.
- Recirculation-adjacent rows are not ordinary single-stream closure fits.

## Validation

- `python -m py_compile tools/extract/sample_minor_loss_two_tap.py tools/extract/test_sample_minor_loss_two_tap.py`: passed.
- `python -m pytest tools/extract/test_sample_minor_loss_two_tap.py -q`: `5 passed`.
- `python tools/extract/sample_minor_loss_two_tap.py`: generated the target
  package.

## Recommended Next Action

Run a follow-up raw two-tap extraction for `test_section_complex` and any
reducer/junction taps with explicit centerline tap-to-tap length, then refresh
the pressure ledger's minor-loss column from `K_local` rather than legacy
`K_apparent`.
