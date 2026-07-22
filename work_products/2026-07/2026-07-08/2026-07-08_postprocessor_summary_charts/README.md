# Postprocessor Summary Charts

Generated: `2026-07-09T10:52:20`
Task: `TODO-POSTPROCESSOR-CHARTS`

## Scope

This package creates tomorrow-facing charts from existing postprocessor evidence
without new OpenFOAM-heavy extraction. It is a scientific communication package,
not a new closure fit.

## Evidence Classes

- Salt 2/3/4 Jin mainline pressure, heat, friction, and upcomer rows are
  admitted mainline evidence, but still carry the `coarse_no_gci` limitation.
- Corrected Salt Q rows are live/status evidence only and remain excluded from
  closure fitting until formal gate requalification.
- F5/Ri is a failed candidate screen on the current admitted dataset; it is
  not a validated Richardson-number law.

## Figures

- `figures/mechanical_pressure_terms_by_span.svg`: Mechanical pressure terms are ordinary-sized across the main spans once signed p_rgh density-gradient source terms are separated from irreversible loss. Caveat: Development/reset and minor-loss upper-bound bars are diagnostic estimates and should not be added to the de-buoyed friction target.
- `figures/pressure_decomposition_by_span.svg`: Pressure evidence is now decomposed into mechanical loss, buoyancy, development/reset, feature-loss upper bounds, and residual rather than raw p_rgh slopes. Caveat: Coarse mesh only; recirculation spans and minor-loss upper bounds must not be promoted to universal friction coefficients.
- `figures/heat_source_sink_by_patch_group.svg`: The loop heat balance is near closed at the wall-flux level, but the test section is a net sink and passive/junction losses are first-order thermal-state evidence. Caveat: Patch-group wall flux is not the same quantity as the segment enthalpy residual; use the residual chart for segment closure.
- `figures/heat_enthalpy_residual_by_segment.svg`: Span endpoint temperatures now quantify lower-leg, cooling-branch, downcomer, and upcomer heat residuals separately from patchwise wall-flux accounting. Caveat: Upcomer residuals are recirculation diagnostics, cooler spans only partially bracket the cooler, and junction rows remain unbracketed.
- `figures/friction_form_mdot_error.svg`: Developing-flow friction forms reduce the F1 mass-flow overprediction, but hydraulic success cannot be separated from thermal-state matching yet. Caveat: Matched insulation values are diagnostic and should not be confused with a fully audited physical scenario contract.
- `figures/friction_per_leg_pressure_drop.svg`: The per-leg comparison shows why F4_leg_class suppresses mdot: it adds large heater/downcomer resistance relative to F3 forms. Caveat: These are 1D solver terms, not direct CFD pressure-ledger terms.
- `figures/f5_ri_screen_coefficients.svg`: The current admitted dataset does not support a 1-parameter Ri multiplier; F5 is a scaffold for future gated perturbation data, not a result. Caveat: Three points per leg class and no independent validation; corrected Salt gate must finish before refitting.
- `figures/upcomer_backflow_vs_re.svg`: Backflow weakens from Salt 2 to Salt 4 as Re increases, supporting a separate upcomer regime treatment. Caveat: Only three coupled operating points; onset predictions are extrapolated and need corrected-Q or new CFD design points.
- `figures/corrected_salt_gate_status.svg`: Some corrected Salt rows show expected mdot movement, but formal gate completion and special-scrutiny disposition are still required. Caveat: Do not use this chart as closure-fit evidence.

## Source Inventory

- `pressure_ledger`: `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv` — Primary pressure decomposition table for admitted Salt 2/3/4 spans.
- `pressure_readme`: `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/README.md` — Pressure equations, sign convention, and caveats.
- `heat_ledger`: `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv` — Primary patchwise heat source/sink table for admitted Salt 2/3/4 rows.
- `heat_readme`: `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/README.md` — Heat sign convention, wall-flux/enthalpy boundary, and caveats.
- `observations`: `work_products/2026-07/2026-07-08/2026-07-08_closure_observation_table/closure_observations.csv` — Canonical observation/admission schema summary.
- `friction_mdot`: `work_products/2026-07/2026-07-07/2026-07-07_friction_forms_comparison/mdot_comparison.csv` — AGENT-195 1D friction-form mdot and per-leg pressure-drop comparison.
- `f5_fit`: `work_products/2026-07/2026-07-07/2026-07-07_f5_ri_corrected/f5_fit_summary.csv` — AGENT-200 Ri-corrected F5 candidate-screen coefficients.
- `f5_mdot`: `work_products/2026-07/2026-07-07/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv` — AGENT-200 confirmation that F5 currently equals F3 Shah apparent.
- `upcomer_dataset`: `work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv` — AGENT-196 upcomer recirculation/regime dataset.
- `upcomer_fit`: `work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv` — AGENT-196 three-point backflow trend and onset caveats.
- `corrected_salt_monitor`: `work_products/2026-07/2026-07-07/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv` — AGENT-181 live corrected-Salt status monitor; status-only, not closure evidence.

## Observed Facts

- July 8 pressure ledger contributes 18 admitted Salt 2/3/4 span rows with explicit buoyancy, distributed loss, development/reset, minor-loss upper-bound, and residual terms.
- July 8 patchwise heat ledger contributes 15 patch-group rows; aggregate heater input, cooler/passive removals, and segment enthalpy residuals are available as validation diagnostics.
- Heat enthalpy residuals are populated for non-junction spans; current absolute residuals range from 36.7 W to 162.7 W.
- F1 mdot errors are positive across Salt 2/3/4 (9.7% to 18.0%), while F3 Shah apparent narrows the range (-0.9% to 3.7%).
- F4 leg-class mdot errors are negative across Salt 2/3/4 (-24.7% to -23.2%), consistent with over-stiffening in the current 1D run.
- F5/Ri screen has 4 leg classes either deactivated or excluded; active F5 coefficients are zero in the current package.
- Upcomer backflow fraction decreases across the admitted Salt series from 27.8% to 17.2% as Re increases.
- Corrected Salt live monitor includes 14 status rows; 4 need special gate scrutiny and 2 are marked investigate.

## Inferred Interpretation

- The strongest presentable story is decomposition and admission discipline: the workflow now separates what CFD directly shows from terms that can become 1D closures.
- Developing-flow friction is already a better practical baseline than fully developed F1 for the current Salt 2/3/4 mdot screen.
- The remaining mdot gap cannot be assigned to friction alone because the heat ledger now shows first-order segment enthalpy residuals and a net-sink test-section wall flux.
- The upcomer should be treated as a regime problem, not as an ordinary single-stream pipe-friction span, until recirculation onset is better bounded.
- Corrected Salt perturbations are promising for expanding the operating envelope but remain outside closure fitting until formal gate requalification.

## Blockers / Work In Progress

- No mesh/GCI uncertainty is attached to the presented QOIs yet; all admitted rows remain coarse_no_gci.
- Corrected Salt perturbation rows are status-only until the gate completes and special-scrutiny rows are dispositioned.
- Thermal enthalpy residuals are available for non-junction spans, but upcomer rows are recirculation diagnostics and cooler endpoints only partially bracket the cooler.
- F5/Ri cannot be promoted without more admitted operating points spanning a wider Ri/Re domain.

## Recommended Next Actions

- Use this chart package for tomorrow's high-level evidence story: pressure decomposition, heat accounting, friction screens, upcomer regime, and gate status.
- Use the enthalpy-residual chart to separate thermal-state mismatch from pressure and mdot model-form scores.
- Build the model-form bakeoff from the closure observation table, scoring pressure distribution, mdot, and thermal-state mismatch separately.
- When corrected Salt gate results land, refresh the status chart first, then decide which rows may enter perturbation trend and F5/Ri refit packages.
- Pursue mesh/GCI intake before making paper-grade coefficient claims.

## Reproduce

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python tools/analyze/build_postprocessor_summary_charts.py
python -m pytest tools/analyze/test_postprocessor_summary_charts.py -q
```
