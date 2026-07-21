# CFD-Informed Fixed-mdot 1D Background Runs

Date: `2026-07-08`
Task: `AGENT-211`
Owner: codex

## Work Performed

Claimed a local `ethan_runs` task because `AGENT-210` already owns the external
Fluid solver files.  Implemented a local fixed-mdot replay harness that imports
Fluid read-only, holds Salt 2/3/4 mdot at the CFD observation, solves thermal
periodicity through Fluid `pressure_residual(...)`, and reports pressure
residuals diagnostically.

Spawned read-only helper audits for the prepared AGENT-209 prompts:

- cooler/HX duty audit,
- source/test-section contract audit,
- radiation/`qr` reconstruction,
- fixed-mdot Fluid solver design.

Integrated those findings into the run matrix and documentation.

## Run Command

Final provenance-correct run:

```bash
srun -n 1 env PYTHONUNBUFFERED=1 python tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py --output-dir work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs
```

The final run completed in Slurm job `3282230`, step `1`.

## Key Results

The output package is:

- `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/`

Counts:

- `run_plan_rows = 21`
- `result_rows = 21`
- `path_summary_rows = 7`

Best path:

- `P1_cfd_cooler_duty_only`
- mean abs Tmean error: `4.456 K`
- max abs Tmean error: `6.219 K`
- mean abs loop-dT error: `0.140 K`
- pressure residual remains diagnostic, mean abs `31.849 Pa`

No path passed the strict `2 K` mean-T / `1 K` loop-dT gate.

## Detailed Provenance Addendum

This work was intentionally implemented in `ethan_runs`, not in the external
Fluid repository, because `AGENT-210` had active ownership of
`../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
and related Fluid tests.  The local wrapper therefore treated Fluid as
read-only and called existing public/internal functions:

- `pressure_residual(...)`
- `solve_temperature_periodicity(...)`, through the pressure-residual helper
- `build_geometry(refinement=default_geometry_refinement())`
- `MinorLosses()` with default coefficients

Input tables consumed directly:

- `work_products/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv`
  for Salt 2/3/4 CFD mdot, mean temperature, and loop Delta T targets.
- `work_products/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv`
  for heater, cooler, passive-wall, test-section, and junction heat-contract
  rows.
- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
  as the upstream source of patch roles, sign convention, wallHeatFlux totals,
  missing-`qr` caveat, and resistance-network diagnostics.
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`
  indirectly through the thermal-boundary and heat-ledger products that define
  span enthalpy residual caveats.
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_solver_plan.md`
  for the requested fixed-mdot algorithm and acceptance boundary.
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/parallel_agent_prompts.md`
  for the helper-audit work streams.

Read-only Fluid/source files inspected or depended on:

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/geometry.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`

Run environment recorded by `run_metadata.json`:

- Host: `c318-008.ls6.tacc.utexas.edu`
- Slurm job: `3282230`
- Slurm step: `1`
- Python: `3.9.7`
- `ethan_runs` git revision recorded by runner:
  `449e9a61c97f8ddbab14a8f1b5ab0b2a6192dfa8`
- Fluid git revision recorded by runner:
  `34af0397beadcd00e7d1f6520f01ff3946209aa9`

Important environment note: direct `python3.11` on this node did not have
`numpy`, so numerical Fluid runs used the loaded TACC `python3/3.9.7` module
available as `python`.  The `python3.11` path was not used for the final Fluid
solve.

## Scenario Matrix Recorded

The final `run_plan.csv` has seven paths for each of Salt 2, Salt 3, and Salt 4:

- `P0_fixed_mdot_current_1d_contract`: current Fluid Salt heat contract at CFD
  mdot.
- `P1_cfd_cooler_duty_only`: current sources, CFD cooler wallHeatFlux magnitude
  imposed as the HX sink.
- `P2_heater_wallflux_no_test_source`: heater wallHeatFlux source, no legacy
  `37 W` test-section source, predictive HX unchanged.
- `P3_source_plus_test_section_sink`: compatibility probe that encodes
  test-section wallHeatFlux as a negative source so Fluid's internal passive
  loss model remains active.
- `P4_cfd_cooler_plus_heater_wallflux`: CFD cooler duty plus heater wallHeatFlux
  source.
- `P5_cfd_cooler_source_plus_test_sink`: preferred source/loss sign-convention
  probe with test-section wallHeatFlux as a positive passive loss; diagnostic
  only because current Fluid prescribed-loss semantics zero unlisted passive
  losses.
- `P6_full_patch_ledger_prescribed`: fixed-Q replay of the mapped patch ledger.

The helper audits explain why these paths were chosen:

- Cooler/HX audit: CFD cooler duty is roughly three times the current Fluid
  predictive HX removal; P1 is therefore the supported immediate replay.
- Source/test-section audit: heater imposed wattage and test-section imposed
  wattage are metadata for CFD replay; Fluid-side replay should use heater
  wallHeatFlux and quartz/test-section wallHeatFlux.
- Radiation audit: no `qr` term is available; do not add radiation on top of
  net wallHeatFlux.
- Fixed-mdot solver-design audit: future Fluid work should add first-class
  fixed-mdot mode and exclude such rows from predictive mdot rankings.

## Limitations To Preserve

- These are fixed-mdot thermal replays, not predictive hydraulic solutions.
  They must not be used to claim that the 1D model predicts mdot.
- Pressure residual is diagnostic only.  It is intentionally not a pass/fail
  gate in this package.
- The best path, `P1_cfd_cooler_duty_only`, still fails the strict mean
  temperature gate: mean absolute Tmean error is `4.456 K`, with max
  `6.219 K`.
- `P1` is not mechanistic cooler prediction.  It prescribes CFD cooler
  wallHeatFlux magnitude, so it diagnoses the missing sink but does not replace
  the need for a predictive cooler/removal model.
- `P5` expresses the preferred sign convention for the quartz sink, but current
  Fluid loss-map semantics make it nonphysical when only the test-section loss
  is supplied.  This is a solver capability finding, not evidence against the
  split source/loss contract.
- `P6` is a fixed-Q energy replay.  Its good loop-Delta-T behavior does not
  imply a valid mean-temperature closure because fixed heat rates under-anchor
  the periodic thermal solution.
- Radiation remains unresolved as a separated component.  The current CFD
  ledger has net `wallHeatFlux` only, no exported patchwise `qr`.
- Mesh uncertainty, latest-window uncertainty, corrected Salt perturbation
  admission, and Salt 1 nominal continuation admission remain outside this
  task.
- External Fluid solver changes were not made because of active ownership by
  `AGENT-210`.

## Cross-References Added

For discoverability, the curated day journal also points to this task:

- `journals/2026-07/2026-07-08_ethan_runs.md`

The more complete scientific narrative is in:

- `operational_notes/07-26/08/2026-07-08_cfd_informed_fixed_mdot_1d_runs.md`

## Interpretation

The cooler path is still the central thermal mismatch.  A replay that only
replaces Fluid's predictive HX duty with the CFD cooler wallHeatFlux magnitude
nearly closes loop delta-T and reduces mean-temperature error from about
`64 K` to about `4.5 K`.  That is a large diagnostic improvement but not a final
mechanistic closure.

The source/test-section audit is physically important: heater imposed duty and
test-section imposed power are solid/electrical metadata, while Fluid-side CFD
replay should use heater wallHeatFlux as source and test-section wallHeatFlux as
loss.  However, the current Fluid prescribed-loss hook is too global for a
single quartz loss because it suppresses unlisted passive losses.

The full fixed-Q ledger is not a predictive external-boundary model.  It can
match loop-dT behavior, but absolute mean temperature becomes under-anchored
without a temperature-dependent resistance network.

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-08_AGENT-211.md`
- `.agent/journal/2026-07-08/cfd-informed-fixed-mdot-1d-background-runs.md`
- `operational_notes/07-26/08/2026-07-08_cfd_informed_fixed_mdot_1d_runs.md`
- `tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py`
- `tools/analyze/test_cfd_informed_fixed_mdot_1d_replays.py`
- `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/**`
- `tmp/2026-07-08_cfd_informed_fixed_mdot_1d_runs/**`

## Validation

```bash
python -m unittest tools.analyze.test_cfd_informed_fixed_mdot_1d_replays
python -m py_compile tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py tools/analyze/test_cfd_informed_fixed_mdot_1d_replays.py
```

Both completed successfully after the final documentation patch.

## Handoff

Recommended next action for the Fluid owner:

1. Add first-class `hydraulic_solution_mode` and `fixed_mdot_kg_s` metadata.
2. Ensure fixed-mdot rows are excluded from predictive mdot rankings.
3. Fix prescribed segment loss semantics so a local quartz sink can coexist with
   internally modeled unlisted passive losses.
4. Rebuild a temperature-dependent cooler/passive boundary network before
   using these rows in model-form bakeoff.
