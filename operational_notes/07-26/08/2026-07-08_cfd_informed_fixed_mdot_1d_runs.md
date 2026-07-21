# CFD-Informed Fixed-mdot 1D Thermal Replay Runs

Date: `2026-07-08`
Task: `AGENT-211`
Role: Coordinator / Implementer / Writer

## Scope

This note records the first executable 1D replay runs that hold the hydraulic
state at the CFD-observed Salt mass flow and vary only the thermal boundary
contract.  The purpose is not to claim a predictive hydraulic closure.  The
purpose is to isolate thermal-state mismatch before the model-form bakeoff,
because prior predictive 1D rows were simultaneously changing heat loss,
density, viscosity, buoyancy, pressure loss, and mdot.

Output package:

- `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/`
- Runner: `tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py`
- Tests: `tools/analyze/test_cfd_informed_fixed_mdot_1d_replays.py`

The run executes the algorithm proposed in:

- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_solver_plan.md`

It does so as a local wrapper because `AGENT-210` currently owns the external
Fluid solver files, including `solver.py`.  No external Fluid source file is
edited by this task.

## Input Provenance

Primary CFD-informed inputs:

- `work_products/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv`
- `work_products/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv`
- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`

Relevant prior analysis:

- `operational_notes/07-26/08/2026-07-08_thermal_boundary_contract_and_frozen_replay_plan.md`
- `operational_notes/07-26/08/2026-07-08_thermal_mismatch_remedy_deep_dive.md`
- `operational_notes/07-26/08/2026-07-08_test_section_heat_contract_and_analysis_plan.md`

Read-only 1D model source:

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/geometry.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`

The exact git revisions are written by the runner into
`run_metadata.json` when the replay finishes.

## Solver Procedure

The local runner imports Fluid read-only and executes one fixed-mdot evaluation
per case/path:

1. Read the Salt 2/3/4 CFD targets from `case_thermal_targets.csv`.
2. Build Fluid's default refined 1D geometry.
3. Apply the same non-test-section insulation rewrite used inside Fluid
   `solve_case()`.
4. Set `mdot = cfd_mdot_kg_s`.
5. Call Fluid `pressure_residual(mdot, ...)` once.
6. Use the returned `ThermalClosureResult` from
   `solve_temperature_periodicity(...)`.
7. Record `deltaP_losses_Pa`, `deltaP_buoyancy_Pa`, and
   `pressure_residual_Pa = deltaP_losses_Pa - deltaP_buoyancy_Pa` as diagnostics.
8. Do not call Fluid's mdot scan and do not reject a thermal replay because the
   pressure residual is nonzero.

The pressure residual is scientifically useful because it says what the current
hydraulic closure would have wanted to do at the CFD mdot.  It is not a score
for these rows.

## Solver Settings

The base 1D scenario is:

- `ambient_temperature_K = 300.0`
- `insulation_thickness_in = 1.0`
- `radiation_on = True`
- `model_mode = predictive_airside_hx` unless a path imposes CFD cooler duty
- `air_counterflow = True`
- `max_outer_iterations = 80`
- `MinorLosses()` default hydraulic coefficients
- Fluid default geometry refinement

The numerical environment used for the runnable path is the loaded TACC
`python3/3.9.7` module, exposed as `/usr/bin/python` in this allocation.  This
environment has `numpy 1.21.2` and `pandas 1.3.3`.  The direct `python3.11`
binary on the node lacks `numpy`; it was therefore used only for tests that do
not import Fluid.

## Thermal Path Matrix

The package writes `run_plan.csv` with seven paths for Salt 2/3/4.

| Path | Thermal contract | Interpretation |
| --- | --- | --- |
| P0 | Current Fluid Salt inputs: heater imposed duty plus `37 W` test-section source, predictive air-side HX, internal passive losses | Baseline fixed-mdot thermal replay |
| P1 | Current sources, but impose CFD cooler wallHeatFlux magnitude as `qhx` | Dominant cooler-duty remedy |
| P2 | Heater interface wallHeatFlux as source; remove `37 W` test-section source; predictive HX remains | Source-contract probe |
| P3 | Heater wallHeatFlux plus test-section wallHeatFlux encoded as a negative source | Compatibility probe that keeps internal passive-loss model active |
| P4 | CFD cooler duty plus heater wallHeatFlux; omit `37 W` test-section source | Combined cooler/source probe |
| P5 | CFD cooler duty, heater wallHeatFlux source, test-section wallHeatFlux as positive passive loss | Preferred source/loss sign-convention probe, with current Fluid prescribed-loss caveat |
| P6 | Heater wallHeatFlux plus all mapped CFD cooler/passive/test/junction losses as fixed segment losses | Full fixed-Q ledger replay; mean temperature is under-anchored without temperature-dependent boundaries |

P5 reflects the source/test-section audit result: imposed heater and
test-section powers are solid/electrical metadata, while Fluid-side replay
should use heater wallHeatFlux as the source and net quartz wallHeatFlux as a
loss.  P3 is retained only because current Fluid loss-prescription semantics
make unlisted passive losses zero once a prescribed loss map is supplied.

## Radiation Accounting

The radiation audit confirms that `wallHeatFlux` is the total net fluid-side
wall flux available from these CFD outputs.  No OpenFOAM `qr` output field is
available for Salt 2/3/4.  Therefore this replay does not add a separate
radiation term on top of prescribed CFD `wallHeatFlux`.

For future decomposition, radiation must be exported from the boundary
condition or reconstructed with the boundary-condition algebra.  Until that
exists, emissivity metadata is not a measured radiation heat ledger term.

## Background Run

The replay was launched on the current allocated node with:

```bash
srun -n 1 env PYTHONUNBUFFERED=1 python tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py --output-dir work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs
```

The first attempt to detach with shell backgrounding did not produce a durable
log in this command wrapper.  The active run is therefore managed as an `srun`
tool session and polled until completion.  The final provenance-correct run
completed as Slurm job `3282230`, step `1`, on host
`c318-008.ls6.tacc.utexas.edu`.  The package metadata records:

- `generated_utc = 2026-07-08T20:29:01+00:00`
- `python = 3.9.7`
- `run_plan_rows = 21`
- `result_rows = 21`
- `path_summary_rows = 7`
- `pressure_policy = diagnostic_only_not_rooted`

Final result files:

- `fixed_mdot_pressure_replay_results.csv`
- `path_summary.csv`
- `run_metadata.json`
- `README.md`

## Results

Aggregate path results:

| Path | Mean abs Tmean error K | Max abs Tmean error K | Mean abs loop dT error K | Mean abs pressure residual Pa | Thermal gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| P0 | 63.746 | 65.026 | 1.075 | 30.469 | false |
| P1 | 4.456 | 6.219 | 0.140 | 31.849 | false |
| P2 | 34.097 | 36.937 | 1.684 | 21.827 | false |
| P3 | 28.459 | 28.679 | 1.591 | 20.824 | false |
| P4 | 39.749 | 40.875 | 0.580 | 3.017 | false |
| P5 | 91.587 | 179.273 | 0.669 | 3359.861 | false |
| P6 | 128.890 | 168.296 | 0.324 | 2537.192 | false |

Observed interpretation:

- P1 remains the best thermal replay: prescribing only the CFD cooler duty
  reduces mean-temperature error from about `64 K` to `4.46 K` while keeping
  loop delta-T error near `0.14 K`.
- P1 still misses the strict `2 K` mean-temperature gate, so it is a strong
  diagnostic remedy but not a final mechanistic closure.
- P4 shows that combining CFD cooler duty with heater wallHeatFlux overcools by
  about `40 K`.  This means the source and sink fixes cannot be linearly stacked
  without a temperature-dependent passive boundary network.
- P5 is the preferred source/loss sign convention in principle, but current
  Fluid prescribed-loss semantics make unlisted passive losses zero.  Salt 2
  falls into an unphysical low-temperature non-rooted state, so P5 is a solver
  capability diagnostic rather than a closure candidate.
- P6 again shows the fixed-Q full ledger is useful for loop delta-T but
  under-anchors absolute mean temperature unless heat losses depend on surface,
  ambient, and wall temperatures.
- Pressure residuals are reported in every row but are not used for pass/fail in
  this package.

## Fit and Validation Boundary

These rows support thermal-state diagnosis and future closure design.  They do
not support a statement that the 1D model predicts mdot.  Any later
model-form bakeoff must keep three score groups separate:

- pressure distribution and pressure residual under predictive hydraulics,
- mdot prediction under predictive hydraulics,
- thermal-state mismatch under fixed-mdot replay or predictive replay.

The immediate scientific use is to decide which thermal boundary contract
should be implemented before retuning friction closures.

## Helper-Audit Findings Integrated

Read-only helper agents inspected the parallel prompts from AGENT-209:

- Cooler/HX audit: CFD cooler duty is roughly three times the current Fluid
  predictive `qhx`; P1 is therefore the supported immediate thermal replay
  remedy. Predictive HX changes should be narrow: configurable active length,
  shell geometry, reducer-area accounting, and honoring `air_counterflow`.
- Source/test-section audit: for CFD replay use a split solid/fluid contract;
  heater imposed duty remains metadata, heater wallHeatFlux is the Fluid-side
  source, and the quartz test-section net sink should be a positive passive
  loss.
- Radiation audit: no `qr` field is present; do not double count emissivity by
  adding radiation to net wallHeatFlux.
- Fixed-mdot solver-design audit: first-class Fluid implementation should add
  `hydraulic_solution_mode` and `fixed_mdot_kg_s`, mark pressure residuals as
  diagnostic, and exclude fixed-mdot replay rows from predictive rankings.

## Validation Commands

```bash
python -m unittest tools.analyze.test_cfd_informed_fixed_mdot_1d_replays
python -m py_compile tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py tools/analyze/test_cfd_informed_fixed_mdot_1d_replays.py
python tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py --output-dir tmp/2026-07-08_cfd_informed_fixed_mdot_1d_runs/python39_plan_smoke_v2 --plan-only
```

All three validation commands completed successfully before the full `srun`
replay was launched.  After the final documentation patch, the focused unittest
and syntax checks were rerun and passed again:

```bash
python -m unittest tools.analyze.test_cfd_informed_fixed_mdot_1d_replays
python -m py_compile tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py tools/analyze/test_cfd_informed_fixed_mdot_1d_replays.py
```

## Recommended Next Action

After this run completes, inspect `path_summary.csv`.  If P1/P4/P5 remain the
only low-mean-temperature-error families, the next implementation step is not a
friction fit.  It is a Fluid-owned thermal-boundary patch: first-class
fixed-mdot replay metadata, split source/loss contract ingestion, and a
temperature-dependent cooler/passive boundary network that can reproduce the
CFD wallHeatFlux ledger without prescribing every heat rate as fixed `Q`.
