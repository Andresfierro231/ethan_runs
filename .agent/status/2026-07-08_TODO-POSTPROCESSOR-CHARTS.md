# TODO-POSTPROCESSOR-CHARTS Status

Date: `2026-07-08`
Role: Implementer / Writer
Owner: codex

## Scope

Create a reproducible, read-only chart and analysis package from existing
postprocessor evidence for tomorrow's presentation and later thesis/journal
use.

Editable paths:

- `.agent/BOARD.md` own row only
- `.agent/status/2026-07-08_TODO-POSTPROCESSOR-CHARTS.md`
- `.agent/journal/2026-07-08/postprocessor-summary-charts.md`
- `tools/analyze/build_postprocessor_summary_charts.py`
- `tools/analyze/test_postprocessor_summary_charts.py`
- `work_products/2026-07-08_postprocessor_summary_charts/**`

## Completed

- Added `tools/analyze/build_postprocessor_summary_charts.py`, a read-only
  standard-library chart/package builder.
- Added `tools/analyze/test_postprocessor_summary_charts.py`.
- Generated `work_products/2026-07-08_postprocessor_summary_charts/**`.
- Wrote seven SVG figures:
  - `figures/pressure_decomposition_by_span.svg`
  - `figures/heat_source_sink_by_patch_group.svg`
  - `figures/friction_form_mdot_error.svg`
  - `figures/friction_per_leg_pressure_drop.svg`
  - `figures/f5_ri_screen_coefficients.svg`
  - `figures/upcomer_backflow_vs_re.svg`
  - `figures/corrected_salt_gate_status.svg`
- Wrote provenance and reduced-data tables:
  - `source_inventory.csv`
  - `figure_manifest.csv`
  - `tables/pressure_terms_summary.csv`
  - `tables/heat_terms_summary.csv`
  - `tables/friction_mdot_summary.csv`
  - `tables/f5_fit_screen_summary.csv`
  - `tables/upcomer_regime_summary.csv`
  - `tables/corrected_salt_status_summary.csv`
  - `tables/observation_table_summary.csv`
- Wrote narrative files:
  - `README.md`
  - `presentation_story.md`
  - `thesis_story.md`
  - `trends_and_next_analysis.md`
  - `summary.json`

## Current State

Complete. The package is suitable for tomorrow-facing presentation use as a
carefully caveated evidence summary. It is not a new closure fit.

## Evidence Inputs

- `work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_closure_observation_table/closure_observations.csv`
- `work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv`
- `work_products/2026-07-07_f5_ri_corrected/f5_fit_summary.csv`
- `work_products/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv`
- `work_products/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv`
- `work_products/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv`
- `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`

## Acceptance Targets

- Generate charts from existing CSV/JSON evidence only.
- Label admitted Salt 2/3/4 mainline data separately from status-only corrected
  Salt rows.
- Emit source-data summaries, figure manifest, README, presentation story, and
  thesis story notes.
- Record observed facts, inferred interpretation, blockers, and recommended next
  actions.

All acceptance targets are met.

## Observed Facts

- July 8 pressure ledger contributes 18 admitted Salt 2/3/4 span rows with
  explicit buoyancy, distributed loss, development/reset, minor-loss upper-bound,
  and residual terms.
- July 8 patchwise heat ledger contributes case/patch-group wall-flux accounting
  for heater, cooler, ambient wall, test section, and junction/other roles.
- F1 mdot errors are positive across Salt 2/3/4 (`+9.7%` to `+18.0%`), while
  F3 Shah apparent narrows the range (`-0.9%` to `+3.7%`).
- F4 leg-class mdot errors are negative across Salt 2/3/4 (`-24.7%` to
  `-23.2%`), consistent with over-stiffening in the current 1D run.
- F5/Ri active coefficients are zero; F5 remains a failed candidate screen, not
  a validated Ri law.
- Upcomer backflow fraction decreases from `27.8%` to `17.2%` across the admitted
  Salt series as Re increases.
- Corrected Salt live monitor includes 14 status rows; 4 need special scrutiny
  and 2 are marked investigate.

## Inferred Interpretation

- The strongest presentable story is now decomposition and admission discipline:
  CFD evidence is separated into pressure, heat, friction-form, upcomer-regime,
  and gate-status layers.
- Developing-flow friction is a better current practical baseline than fully
  developed F1, but mdot cannot be used as a standalone friction validation
  score while the 1D thermal state is mismatched.
- The upcomer should remain a regime problem rather than an ordinary
  single-stream pipe-friction fit target.

## Blockers / Work In Progress

- No mesh/GCI uncertainty is attached to the presented QOIs yet.
- Corrected Salt perturbation rows remain status-only until formal gate
  requalification and special-scrutiny disposition.
- Heat-ledger enthalpy residuals still depend on span inlet/outlet bulk
  temperatures.
- F5/Ri needs more admitted operating points before refit or promotion.

## Validation

- `python -m py_compile tools/analyze/build_postprocessor_summary_charts.py tools/analyze/test_postprocessor_summary_charts.py`: passed.
- `python -m pytest tools/analyze/test_postprocessor_summary_charts.py -q`: 3 passed.
- `python tools/analyze/build_postprocessor_summary_charts.py`: generated the
  package successfully.

## Recommended Next Action

Use this package for tomorrow's presentation story, then continue with endpoint
bulk-temperature extraction, heat-ledger enthalpy residual closure, and the
model-form bakeoff from the closure observation table.
