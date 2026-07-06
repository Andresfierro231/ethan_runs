# AGENT-126 Raw Journal — Presentation Salt Cards And Energy Note

Date: `2026-06-23`
Task ID: `AGENT-126`
Owner: `codex`
Role: `Coordinator / Implementer / Writer`

## Intent

Produce a presentation-local follow-on to the existing Slide 10 summary:

- add Salt `1-4` metric cards using the current defended June 23 1D-vs-frozen
  CFD surface
- write the exact energy-error formula in the local presentation
  documentation so slide notes and verbal explanation stay aligned with code

## Inputs Confirmed

- `tools/analyze/build_ethan_presentation_refresh.py`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/surface_summary.csv`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/scenario_shadow_summary.csv`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/defended_full_coverage_surface/case_metric_summary.csv`
- `tools/analyze/build_ethan_frozen_state_1d_validation_package.py`

## Working Assumption

For a `Salt 1-4` progression card set, use the `Jin` family rows from the
defended full-coverage baseline scenario because they are the only readable
set that spans all four Salt numbers on one consistent scenario surface.

## Work Completed

- Patched `tools/analyze/build_ethan_presentation_refresh.py` to generate
  `D_salt1to4_metric_cards` from
  `reports/2026-06-23_ethan_1d_closure_bakeoff/defended_full_coverage_surface/case_metric_summary.csv`.
- Added backup-slide documentation and the new manifest entry inside
  `reports/2026-06-23_presentation/**`.
- Added the exact score definition:
  - `energy_error_w = (qhx_total_W + qambient_total_W) - (cfd_removed_w + cfd_ambient_w)`
  - `energy_error_pct_of_heater = 100 * abs(energy_error_w) / abs(cfd_heater_w)`

## Execution Notes

- `python3.11` failed for figure generation because `matplotlib` is absent in
  that interpreter on this machine.
- The working regeneration path was:
  - `python -m py_compile tools/analyze/build_ethan_presentation_refresh.py`
  - `python tools/analyze/build_ethan_presentation_refresh.py`

## Output Checked

- `reports/2026-06-23_presentation/figures/png/D_salt1to4_metric_cards.png`
- `reports/2026-06-23_presentation/figures/pdf/D_salt1to4_metric_cards.pdf`
- `reports/2026-06-23_presentation/figures/figure_manifest.csv`
