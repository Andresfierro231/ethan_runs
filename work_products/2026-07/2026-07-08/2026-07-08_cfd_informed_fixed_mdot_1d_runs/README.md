# CFD-Informed Fixed-mdot 1D Replay Run Package

Generated: `2026-07-08T20:29:01+00:00`
Task: `AGENT-211`

## Purpose

These runs execute the fixed-mdot thermal replay proposed by `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_solver_plan.md` while avoiding edits to the externally owned Fluid solver. The goal is to separate thermal boundary-condition replay from predictive hydraulic scoring: the Salt CFD mdot is imposed, thermal periodicity is solved, and the pressure residual is reported but not used to move mdot.

## Solver Contract

- 1D solver source: read-only `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`.
- Thermal root: `solve_temperature_periodicity(...)`, called through `pressure_residual(...)`.
- Hydraulic state: `fixed_mdot_kg_s = cfd_mdot_kg_s` from `case_thermal_targets.csv`.
- Pressure diagnostic: `pressure_residual_Pa = deltaP_losses_Pa - deltaP_buoyancy_Pa`; no pressure-root search is performed.
- Geometry: Fluid default refined geometry with the same non-test-section insulation rewrite used in `solve_case()`.
- Minor losses: default `MinorLosses()`; no CFD minor-loss closure is injected in this thermal replay package.
- Radiation: Fluid external radiation switch remains on for internal boundary-model paths, but CFD `qr` is not prescribed because the patchwise ledger reports no exported `qr` field.

## Scenario Matrix

`run_plan.csv` contains seven thermal-input paths for Salt 2/3/4. Paths P0-P4 retain temperature-dependent 1D passive loss models except where a CFD cooler duty is imposed. P5 uses the preferred split source/loss sign convention for the quartz test-section sink, but current Fluid prescribed-loss semantics zero unlisted passive losses once a loss map is supplied. P6 prescribes the full patchwise ledger as fixed heat rates; it is a diagnostic energy replay rather than a predictive external-boundary model because fixed-Q losses cannot anchor absolute mean temperature without a temperature-dependent resistance network.

## Output Files

- `run_plan.csv`: cases and thermal-input policies submitted to the background run.
- `fixed_mdot_pressure_replay_results.csv`: per-case replay outputs with thermal errors and diagnostic pressure residuals.
- `path_summary.csv`: aggregate thermal and pressure-residual diagnostics by path.
- `run_metadata.json`: command, host, Python, Fluid source, and input provenance.

## Interpretation Boundary

These rows are eligible for thermal-state diagnosis and model-form design, not for mdot predictivity claims. A later Fluid-owned implementation of `fixed_mdot_kg_s` in `ScenarioConfig` should reproduce the thermal values here and add first-class result metadata so reporting layers cannot mix fixed-mdot replay scores with predictive hydraulic scores.
