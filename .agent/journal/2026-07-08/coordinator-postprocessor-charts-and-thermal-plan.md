# Coordinator Postprocessor Charts And Thermal Plan

Date: `2026-07-08`
Agent role: Coordinator
Task ID: `TODO-POSTPROCESSOR-CHARTS` planning
Worktree: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/journal/README.md`
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_patchwise_heat_ledger/README.md`
- `work_products/2026-07-08_closure_observation_table/closure_observations.csv`
- `work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv`
- `work_products/2026-07-07_f5_ri_corrected/README.md`
- `work_products/2026-07-07_upcomer_correlation_v2/README.md`
- `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`

## Files Changed

- `.agent/BOARD.md`
- `.agent/journal/2026-07-08/coordinator-postprocessor-charts-and-thermal-plan.md`

## Commands Run

- `sed -n '1,180p' .agent/journal/README.md`
- `rg -n "TODO-POSTPROCESSOR|TODO-MODEL-FORM-BAKEOFF|TODO-MESH-UNCERTAINTY|TODO-PATCHWISE-HEAT-LEDGER|TODO-OBSERVATION-TABLE-CONTRACT" .agent/BOARD.md`
- `sed -n '35,105p' .agent/BOARD.md`
- `ls -la .agent/journal/2026-07-08`
- `nl -ba .agent/BOARD.md | sed -n '68,82p'`
- `sed -n '72,78p' .agent/BOARD.md`
- `sed -n '1,220p' work_products/2026-07-08_patchwise_heat_ledger/README.md`
- `head -5 work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `head -5 work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `head -5 work_products/2026-07-08_closure_observation_table/closure_observations.csv`

## Board Update

Added `TODO-POSTPROCESSOR-CHARTS` as an unclaimed high-priority row. The row is
bounded to `tools/analyze/build_postprocessor_summary_charts.py`,
`tools/analyze/test_postprocessor_summary_charts.py`, and
`work_products/<date>_postprocessor_summary_charts/**`, plus its own status and
journal files.

The chart package should use existing CSV/JSON products and avoid new
OpenFOAM-heavy extraction. It should label admitted Salt 2/3/4 mainline evidence
separately from provisional/status-only rows.

## Readiness Assessment

Ready today:

- Pressure-term decomposition charts from the completed July 8 pressure ledger.
- Heat-source/sink charts from the completed July 8 patchwise heat ledger.
- Friction-form mdot error and per-leg pressure-drop charts from AGENT-195.
- Upcomer recirculation/regime charts from AGENT-196.
- Corrected Salt live/gate status charts as status-only evidence.

Not ready as closure-grade charts:

- Corrected Salt perturbation closure trends, because the gate is still pending.
- Mesh/GCI uncertainty bands, because mesh levels remain unresolved.
- Heat-ledger enthalpy residual charts, because inlet/outlet bulk temperatures
  are missing from the patchwise heat ledger.
- Universal Ri or mixed-convection friction correlation charts, because F5 was
  a failed 3-point screen and perturbation data is not admitted.

## Thermal State Mismatch Plan

The 1D thermal state mismatch should be solved before mdot is used as the main
friction validation score. The practical sequence is:

1. Reconstruct the actual CFD thermal boundary contract in 1D: insulation
   thickness, emissivity/radiation status, ambient temperature, external
   convection coefficients, heater powers, cooler powers, and surface roles.
2. Extract span inlet/outlet bulk temperatures so the patchwise heat ledger can
   compute `enthalpy_change_W` and wall-flux-vs-enthalpy residuals.
3. Run a frozen-hydraulics thermal replay: hold mdot/pressure behavior near CFD
   values and tune only thermal boundary representation until mean temperature
   and loop `Delta T` match CFD.
4. Only after thermal replay passes, rerun the 1D hydraulic model-form bakeoff
   and score mdot, pressure distribution, and thermal state separately.

## Next Figures And Analysis For Tomorrow

Highest-value presentable figures:

- Pressure ledger stacked bars: distributed mechanical loss, density-gradient
  buoyancy, development/reset, minor-loss upper bound, residual/invalid flags.
- Heat ledger stacked bars: heater input, cooler removal, passive ambient loss,
  test-section net exchange, junction/other loss.
- Friction closure chart: mdot error for F1, F3 Hagenbach, F3 Shah apparent,
  F4 leg-class, and F5 screen where applicable.
- Per-leg pressure-drop comparison by friction form.
- Upcomer backflow fraction versus Re with fit caveat and recirculation regime
  label.
- Corrected Salt status timeline/gate chart with closure-fit exclusion labels.

Secondary analysis that can be done today if time remains:

- `TODO-MODEL-FORM-BAKEOFF`: score forms against the completed observation
  table, but keep corrected Salt excluded.
- `TODO-UPCOMER-ONSET`: turn recirculation evidence into a regime table.
- A new enthalpy-endpoint extraction row: produce inlet/outlet bulk temperatures
  needed to close the heat ledger.
- `TODO-MINOR-LOSS-TWO-TAP`: improve feature-loss K estimates for pressure
  decomposition.

## Incomplete Lines

- Mesh/GCI evidence is still not available for closure-grade uncertainty.
- Corrected Salt gate remains the admission blocker for perturbation trends.
- The patchwise heat ledger is strong for wall-flux accounting but intentionally
  does not yet close enthalpy residuals.
