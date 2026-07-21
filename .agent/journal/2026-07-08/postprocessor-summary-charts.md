# Postprocessor Summary Charts

Date: `2026-07-08`
Agent role: Implementer / Writer
Task ID: `TODO-POSTPROCESSOR-CHARTS`
Worktree: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/journal/README.md`
- `tools/AGENTS.override.md`
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07-08_pressure_term_ledger/README.md`
- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_patchwise_heat_ledger/README.md`
- `work_products/2026-07-08_closure_observation_table/closure_observations.csv`
- `work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv`
- `work_products/2026-07-07_friction_forms_comparison/README.md`
- `work_products/2026-07-07_f5_ri_corrected/f5_fit_summary.csv`
- `work_products/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv`
- `work_products/2026-07-07_f5_ri_corrected/README.md`
- `work_products/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv`
- `work_products/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv`
- `work_products/2026-07-07_upcomer_correlation_v2/README.md`
- `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-08_TODO-POSTPROCESSOR-CHARTS.md`
- `.agent/journal/2026-07-08/postprocessor-summary-charts.md`
- `tools/analyze/build_postprocessor_summary_charts.py`
- `tools/analyze/test_postprocessor_summary_charts.py`
- `work_products/2026-07-08_postprocessor_summary_charts/README.md`
- `work_products/2026-07-08_postprocessor_summary_charts/source_inventory.csv`
- `work_products/2026-07-08_postprocessor_summary_charts/figure_manifest.csv`
- `work_products/2026-07-08_postprocessor_summary_charts/summary.json`
- `work_products/2026-07-08_postprocessor_summary_charts/presentation_story.md`
- `work_products/2026-07-08_postprocessor_summary_charts/thesis_story.md`
- `work_products/2026-07-08_postprocessor_summary_charts/trends_and_next_analysis.md`
- `work_products/2026-07-08_postprocessor_summary_charts/figures/*.svg`
- `work_products/2026-07-08_postprocessor_summary_charts/tables/*.csv`

## Commands Run

- `sed -n '1,220p' tools/AGENTS.override.md`
- `sed -n '70,80p' .agent/BOARD.md`
- `ls -la work_products/2026-07-07_upcomer_correlation_v2 work_products/2026-07-07_corrected_salt_live_monitor work_products/2026-07-07_f5_ri_corrected work_products/2026-07-07_friction_forms_comparison work_products/2026-07-08_pressure_term_ledger work_products/2026-07-08_patchwise_heat_ledger`
- `head -20 work_products/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv`
- `head -10 work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`
- `head -5 work_products/2026-07-07_f5_ri_corrected/f5_fit_summary.csv`
- `head -5 work_products/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv`
- `head -5 work_products/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv`
- `head -5 work_products/2026-07-08_patchwise_heat_ledger/summary.json`
- `head -5 work_products/2026-07-08_pressure_term_ledger/summary.json`
- `python -m pytest tools/analyze/test_postprocessor_summary_charts.py -q`
- `python -m py_compile tools/analyze/build_postprocessor_summary_charts.py tools/analyze/test_postprocessor_summary_charts.py`
- `python tools/analyze/build_postprocessor_summary_charts.py`
- `find work_products/2026-07-08_postprocessor_summary_charts -maxdepth 2 -type f | sort`
- `sed -n '1,240p' work_products/2026-07-08_postprocessor_summary_charts/README.md`
- `sed -n '1,220p' work_products/2026-07-08_postprocessor_summary_charts/presentation_story.md`
- `sed -n '1,220p' work_products/2026-07-08_postprocessor_summary_charts/thesis_story.md`
- `python -m json.tool work_products/2026-07-08_postprocessor_summary_charts/summary.json`

## Results

Generated seven SVG figures from existing evidence only:

- `pressure_decomposition_by_span.svg`
- `heat_source_sink_by_patch_group.svg`
- `friction_form_mdot_error.svg`
- `friction_per_leg_pressure_drop.svg`
- `f5_ri_screen_coefficients.svg`
- `upcomer_backflow_vs_re.svg`
- `corrected_salt_gate_status.svg`

Generated reduced provenance tables and narrative notes in
`work_products/2026-07-08_postprocessor_summary_charts/`.

Validation:

- Initial focused pytest run found two documentation phrase mismatches; both
  were fixed in the builder so the generated README/presentation draft carry
  the intended explicit caveats.
- Final `python -m pytest tools/analyze/test_postprocessor_summary_charts.py -q`:
  `3 passed`.
- `python -m py_compile ...`: passed.
- `python tools/analyze/build_postprocessor_summary_charts.py`: generated the
  target package successfully.

## Observed Facts

- July 8 pressure ledger contributes 18 admitted Salt 2/3/4 span rows with
  explicit buoyancy, distributed loss, development/reset, minor-loss upper-bound,
  and residual terms.
- July 8 patchwise heat ledger provides wall-flux accounting by physical role:
  heater, cooler, ambient wall, test section, and junction/other.
- F1 mdot errors are positive across Salt 2/3/4 (`+9.7%` to `+18.0%`), while
  F3 Shah apparent narrows the range (`-0.9%` to `+3.7%`).
- F4 leg-class mdot errors are negative across Salt 2/3/4 (`-24.7%` to
  `-23.2%`), consistent with over-stiffening in the current 1D run.
- F5/Ri active coefficients are zero, so F5 currently collapses to F3 Shah
  apparent and is not a validated Ri law.
- Upcomer backflow decreases from `27.8%` to `17.2%` across Salt 2/3/4 as Re
  increases.
- Corrected Salt live monitor has 14 status rows; 4 need special scrutiny and 2
  are marked investigate.

## Inferred Interpretation

- The current presentation should lead with decomposition and admission
  discipline, not with a single new closure coefficient.
- Developing-flow friction is a better current practical baseline than F1, but
  mdot alone cannot validate friction until the thermal state mismatch is
  resolved.
- The upcomer should be modeled as a mixed-convection/recirculation regime, not
  as ordinary single-stream pipe friction.
- Corrected Salt perturbations may expand the operating envelope but remain
  status-only until formal requalification.

## Blockers / Work In Progress

- No mesh/GCI uncertainty is attached to the plotted QOIs yet.
- Corrected Salt rows are not closure-fit admissible yet.
- Heat-ledger enthalpy residuals need span inlet/outlet bulk temperatures.
- F5/Ri needs more admitted operating points spanning a wider Ri/Re domain.

## Recommended Next Action

Use the generated chart package for tomorrow's story, then prioritize endpoint
bulk-temperature extraction, heat-ledger enthalpy residual closure, and the
model-form bakeoff from the closure observation table.
