# Codex Day Provenance Closeout

Date: `2026-07-08`
Role: Coordinator / Writer
Task ID: `AGENT-214`
Branch/worktree: current `ethan_runs` workspace

## Purpose

This closeout records what the Codex-owned work did on July 8, where the
evidence lives, what was inferred from the evidence, and what limitations must
remain attached to the results. It supplements the per-task journals and the
daily rollup rather than replacing them.

## Files Inspected For This Closeout

Coordination and journal state:

- `.agent/BOARD.md`
- `.agent/journal/README.md`
- `.agent/status/README.md`
- `.agent/journal/2026-07-08/coordinator-daily-analysis-rollup-and-presentation-agent-prompt.md`
- `.agent/journal/2026-07-08/thermal-interface-power-policy.md`

Status files:

- `.agent/status/2026-07-08_AGENT-202.md`
- `.agent/status/2026-07-08_AGENT-205.md`
- `.agent/status/2026-07-08_AGENT-206.md`
- `.agent/status/2026-07-08_AGENT-207.md`
- `.agent/status/2026-07-08_AGENT-208.md`
- `.agent/status/2026-07-08_AGENT-209.md`
- `.agent/status/2026-07-08_AGENT-211.md`
- `.agent/status/2026-07-08_AGENT-213.md`

Primary July 8 outputs referenced:

- `work_products/2026-07-08_cfd_scenario_contract/**`
- `work_products/2026-07-08_postprocessor_summary_charts/**`
- `work_products/2026-07-08_thermal_boundary_contract/**`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/**`
- `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/**`
- `operational_notes/07-26/08/2026-07-08_cfd_1d_geometry_bc_contract_and_run_plan.md`
- `operational_notes/07-26/08/2026-07-08_salt1_nominal_continuation_submit.md`
- `operational_notes/07-26/08/2026-07-08_test_section_heat_contract_and_analysis_plan.md`
- `operational_notes/07-26/08/2026-07-08_thermal_boundary_contract_and_frozen_replay_plan.md`
- `operational_notes/07-26/08/2026-07-08_thermal_mismatch_remedy_deep_dive.md`
- `operational_notes/07-26/08/2026-07-08_cfd_informed_fixed_mdot_1d_runs.md`
- `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md`

## Files Changed By This Closeout

- `.agent/BOARD.md`
- `.agent/status/2026-07-08_AGENT-214.md`
- `.agent/journal/2026-07-08/codex-day-provenance-closeout.md`
- `journals/2026-07/2026-07-08_ethan_runs.md`

## What Codex Did Today

### CFD Scenario, Geometry, And Boundary Contract

Relevant tasks: `AGENT-202`, `AGENT-205`.

Outputs:

- `tools/analyze/build_cfd_scenario_contract.py`
- `work_products/2026-07-08_cfd_scenario_contract/scenario_contract.csv`
- `work_products/2026-07-08_cfd_scenario_contract/latest_window_audit.csv`
- `work_products/2026-07-08_cfd_scenario_contract/closure_observations_seed.csv`
- `operational_notes/07-26/08/2026-07-08_cfd_1d_geometry_bc_contract_and_run_plan.md`

Observed facts:

- The audited Salt CFD roots use a `0.03556 m` wall/insulation layer, i.e.
  `1.4 in`.
- The prior `0.25 in` and `0.30 in` values are 1D temperature-matching sweep
  settings, not CFD insulation labels.
- Audited `0/T` files contain `rcExternalTemperature` patches with
  `emissivity 0.95`, but no `constant/radiationProperties`, `qr`, or `G` field
  was found in the audited CFD cases.
- The scenario contract seeded `132` observation rows for later closure work.

Interpretation:

- Salt CFD cases should be labeled as `1.4 in` layer present with emissivity
  metadata but no volume-radiation field.
- 1D scenario settings must not be back-applied as CFD geometry or insulation
  truth.

Limitations:

- This was a read-only audit and seed contract, not final closure fitting.
- Mesh/GCI uncertainty is still open.
- Salt 1 remains less mature than Salt 2/3/4 for closure fitting because of
  window/version caveats.

Validation/provenance:

- `AGENT-202` recorded:
  `python3.11 tools/analyze/build_cfd_scenario_contract.py` passed and
  `python3.11 -m py_compile tools/analyze/build_cfd_scenario_contract.py`
  passed.
- `AGENT-205` recorded live monitor and scheduler checks in
  `tmp/2026-07-08_AGENT-205_live_monitor/**` and checked Slurm gate/dependency
  state for `3275448`, `3275449`, `3275560`, and `3280969`.

### Salt 1 Nominal Continuation Staging

Relevant task: `AGENT-206`.

Outputs:

- `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/**`
- `operational_notes/07-26/08/2026-07-08_salt1_nominal_continuation_submit.md`

Observed facts:

- A corrected Salt 1 nominal continuation candidate was staged from the June 25
  base-continuation candidate.
- Only the copied convergence monitor in the staged candidate was changed to be
  diagnostic-only.
- Submitted Slurm job: `3282992`, job name `salt1_nom_cont`, `1` node,
  `64` ranks, `120:00:00`, initial state `PENDING (Priority)`.

Interpretation:

- The Salt 1 continuation path was made available for future qualification, but
  it is not yet closure evidence.

Limitations:

- No Salt 1 continuation result was available at closeout.
- The source June 25 case tree was not modified.
- Any future Salt 1 use still requires a formal gate and window/admission
  review.

Validation/provenance:

- `AGENT-206` recorded `bash -n` on the launcher, `rg` checks for the
  diagnostic-only convergence monitor, and `squeue -j 3282992`.

### Test-Section Heat Contract And Postprocessor Chart Refresh

Relevant task: `AGENT-207`.

Outputs:

- `operational_notes/07-26/08/2026-07-08_test_section_heat_contract_and_analysis_plan.md`
- `tools/analyze/build_postprocessor_summary_charts.py`
- `tools/analyze/test_postprocessor_summary_charts.py`
- `work_products/2026-07-08_postprocessor_summary_charts/**`

Observed facts:

- The 1D Fluid model applies Salt `test_section_power_W = 37.0 W` as a positive
  source when `segment.has_test_section_heater`.
- The Fluid geometry marks the test section as uninsulated quartz with
  `has_test_section_heater=True`.
- The CFD heat ledger shows Salt 2/3/4 test-section `wallHeatFlux` is negative
  despite the imposed `37 W` gross source.
- The refreshed chart package includes
  `figures/heat_enthalpy_residual_by_segment.svg` and
  `tables/heat_enthalpy_residual_summary.csv`.
- Non-junction absolute heat residuals range from `36.7 W` to `162.7 W`.

Interpretation:

- The 1D gross test-section heat input and net CFD wall heat transfer are not
  interchangeable. Net test-section behavior requires the competing external
  quartz/ambient path.

Limitations:

- Junction residuals remain unbracketed by endpoint enthalpy temperatures.
- Upcomer/test-section residuals are diagnostic-only where recirculation is
  high.
- A predictive test-section closure needs a richer same-time external loss
  stack.

Validation/provenance:

- `AGENT-207` recorded:
  `python tools/analyze/build_postprocessor_summary_charts.py` passed and
  `python -m pytest tools/analyze/test_postprocessor_summary_charts.py`
  passed with `3 passed`.

### Thermal Boundary Contract And Frozen-Replay Plan

Relevant task: `AGENT-208`.

Outputs:

- `tools/analyze/build_thermal_boundary_contract.py`
- `tools/analyze/test_thermal_boundary_contract.py`
- `work_products/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv`
- `work_products/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv`
- `work_products/2026-07-08_thermal_boundary_contract/span_heat_residuals.csv`
- `operational_notes/07-26/08/2026-07-08_thermal_boundary_contract_and_frozen_replay_plan.md`

Observed facts:

- Current CFD Salt thermal contract is classified as
  `cfd_salt_1p4in_layer_present_surface_emissivity_bc_metadata_present_no_qr_field`.
- The prior 1D state is `61.950` to `66.201 K` hotter than CFD and has loop
  Delta T `3.722` to `3.908 K` smaller.
- Heater imposed duty exceeds heater `wallHeatFlux`, and that mismatch is
  preserved as a caveat.
- The current Fluid solver did not yet expose a first-class fixed-mdot thermal
  replay mode.

Interpretation:

- Thermal replay should be separated from hydraulic tuning. The next useful
  step is a frozen-hydraulics/fixed-mdot thermal replay with explicit source
  and sink contracts.

Limitations:

- Current replay planning is not a full predictive physical-system model.
- No separate CFD radiation heat term exists for Salt 2/3/4.
- Full paper-grade replay still requires first-class fixed-mdot solver metadata
  or a reviewed wrapper.

Validation/provenance:

- `AGENT-208` recorded:
  `python3.11 tools/analyze/build_thermal_boundary_contract.py` passed,
  `python3.11 -m unittest tools.analyze.test_thermal_boundary_contract`
  passed with `5/5` focused tests, and `py_compile` passed.

### Thermal Mismatch Remedy Deep Dive

Relevant task: `AGENT-209`.

Outputs:

- `tools/analyze/build_thermal_mismatch_remedy_deep_dive.py`
- `tools/analyze/test_thermal_mismatch_remedy_deep_dive.py`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/heater_values.csv`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_replay_results.csv`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/remedy_path_summary.csv`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/parallel_agent_prompts.md`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_solver_plan.md`
- `operational_notes/07-26/08/2026-07-08_thermal_mismatch_remedy_deep_dive.md`

Observed facts:

- Heater imposed duty versus heater `wallHeatFlux`:
  - Salt 2: `265.700 W` imposed, `243.519 W` into fluid.
  - Salt 3: `297.500 W` imposed, `273.155 W` into fluid.
  - Salt 4: `337.600 W` imposed, `310.487 W` into fluid.
- Current 1D cooler removal is about `46-54 W`.
- CFD cooler `wallHeatFlux` removal is about `136-169 W`.
- Prescribing CFD cooler duty at fixed mdot reduced Salt 2/3/4 mean-temperature
  errors to `6.219`, `4.453`, and `2.697 K`.
- No tested path passed the strict thermal gate.

Interpretation:

- The cooler/HX duty magnitude is the dominant identified thermal mismatch.
- Heater source and test-section sink corrections matter, but stacking all heat
  ledger terms naively can under-anchor mean temperature without a
  temperature-dependent passive boundary network.

Limitations:

- The remedy paths are diagnostic fixed-mdot thermal replays, not committed
  Fluid solver changes.
- The path using full prescribed patch ledger is not an absolute-temperature
  prediction because a periodic fixed-Q solve lacks a temperature-dependent
  external-loss anchor.
- The `qr` radiation term is absent from current CFD output, so radiation cannot
  be separated from net `wallHeatFlux` in current CFD evidence.

Validation/provenance:

- `AGENT-209` recorded:
  `python tools/analyze/build_thermal_mismatch_remedy_deep_dive.py` passed,
  `python3.11 -m unittest tools.analyze.test_thermal_mismatch_remedy_deep_dive`
  passed with `3/3` tests, and `py_compile` passed.

### CFD-Informed Fixed-Mdot Background Runs

Relevant task: `AGENT-211`.

Outputs:

- `tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py`
- `tools/analyze/test_cfd_informed_fixed_mdot_1d_replays.py`
- `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/**`
- `operational_notes/07-26/08/2026-07-08_cfd_informed_fixed_mdot_1d_runs.md`

Observed facts:

- Final background replay completed inside Slurm job `3282230`, step `1`, on
  `c318-008.ls6.tacc.utexas.edu`.
- The final package has `21` run-plan rows, `21` result rows, and `7` path
  summaries.
- All rows hold `mdot = cfd_mdot_kg_s`; pressure residuals are diagnostic.
- Best path by mean absolute Tmean error is `P1_cfd_cooler_duty_only`.
- P1 mean absolute Tmean error is `4.456 K`; max absolute Tmean error is
  `6.219 K`; mean absolute loop-Delta-T error is `0.140 K`.
- No path passed the strict `2 K` mean-temperature and `1 K` loop-Delta-T gate.

Interpretation:

- The cooler/HX duty mismatch remains the dominant thermal-state issue even in
  the more formal background replay package.
- The results should not be used to tune friction. They are thermal replay rows
  with fixed CFD mdot.

Limitations:

- `AGENT-210` owned external Fluid solver files during this work, so `AGENT-211`
  did not edit `solver.py`.
- Fluid still lacks first-class `fixed_mdot_kg_s` / hydraulic mode metadata.
- Fluid prescribed-loss semantics can suppress unlisted passive losses, so some
  split source/loss paths are solver-capability diagnostics rather than closure
  candidates.

Validation/provenance:

- `AGENT-211` recorded:
  `python -m unittest tools.analyze.test_cfd_informed_fixed_mdot_1d_replays`,
  `python -m py_compile ...`, and final
  `srun -n 1 env PYTHONUNBUFFERED=1 python tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py --output-dir work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs`.
- Final metadata records `slurm_job_id=3282230` and `slurm_step_id=1`.

### Thermal Interface Power Policy

Relevant task: `AGENT-213`.

Outputs:

- `.agent/DECISIONS.md`
- `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md`
- `.agent/status/2026-07-08_AGENT-213.md`
- `.agent/journal/2026-07-08/thermal-interface-power-policy.md`

Policy recorded:

- For CFD-informed 3D-to-1D comparison, heater input is the realized CFD heater
  `wallHeatFlux` / `heat_to_fluid_W`, not idealized resistor wattage.
- For CFD-informed 3D-to-1D comparison, cooler removal is the CFD cooler
  `wallHeatFlux` sink magnitude / `cooler_removed_duty_W`, not the current
  idealized 1D cooler-capacity prediction.
- The idealized resistor wattage and idealized cooler model are future
  predictive targets, not current comparison truth.
- Current CFD has emissivity metadata but no `qr`; do not double-count radiation
  when using CFD `wallHeatFlux`.

Future board goals added:

- `TODO-PREDICT-HEATER-FLUID-FRACTION`
- `TODO-PREDICT-COOLER-REMOVAL`
- `TODO-1D-RADIATION-CAPABILITY`

Limitations:

- Current CFD-interface-informed thermal replays are not fully predictive
  simulations from electrical wattage, cooler hardware settings, ambient, and
  geometry.
- Thesis/paper language must disclose this if the heater and cooler predictive
  submodels are not completed and validated.

Validation/provenance:

- `AGENT-213` used targeted `rg` checks to verify that policy rows and terms are
  discoverable from `.agent/BOARD.md`, `.agent/DECISIONS.md`, and the policy
  operational note.

## Cross-Cutting Limitations To Preserve

- **Not all runs are closure evidence.** Salt 2/3/4 Jin continuation rows are
  the current admitted Salt closure evidence. Salt 1 and corrected-Q
  perturbations remain gate/window/status work until formal admission.
- **CFD-informed is not fully predictive.** Replays using CFD heater
  `wallHeatFlux` and CFD cooler duty isolate model behavior, but they do not
  yet predict heater fluid-entry fraction or cooler heat removal from physical
  equipment inputs.
- **Radiation is not a current CFD heat-ledger term.** Surface emissivity
  metadata exists, but no `qr` field was found. 1D radiation capability should
  be developed for sensitivity and forward prediction, reported separately, and
  not double-counted against CFD `wallHeatFlux`.
- **Thermal and hydraulic scores must remain separate.** The thermal mismatch is
  not solved by tuning friction harder. Pressure distribution, mdot, and thermal
  state need separate scores and separate gates.
- **Fixed-mdot replay needs solver support.** The current formal background
  package is useful and documented, but a first-class Fluid fixed-mdot mode and
  clearer prescribed source/loss semantics are still required for paper-grade
  solver provenance.
- **Mesh and time-window uncertainty remain open.** The July 8 work organized
  evidence and rebuilt several ledgers, but it did not complete mesh/GCI
  uncertainty or a final latest-window requalification for every candidate run.

## Commands Run For This Closeout

```bash
sed -n '1,80p' .agent/BOARD.md
ls -la .agent/journal/2026-07-08
find journals -maxdepth 3 -type f | sort
sed -n '1,240p' .agent/journal/2026-07-08/coordinator-daily-analysis-rollup-and-presentation-agent-prompt.md
sed -n '1,220p' .agent/journal/README.md
sed -n '1,220p' .agent/status/README.md
sed -n '1,200p' .agent/status/2026-07-08_AGENT-202.md
sed -n '1,200p' .agent/status/2026-07-08_AGENT-205.md
sed -n '1,200p' .agent/status/2026-07-08_AGENT-206.md
sed -n '1,220p' .agent/status/2026-07-08_AGENT-207.md
sed -n '1,220p' .agent/status/2026-07-08_AGENT-208.md
sed -n '1,220p' .agent/status/2026-07-08_AGENT-211.md
mkdir -p journals/2026-07
```

Final validation commands are recorded in `AGENT-214` status.

## Recommended Next Actions

1. Use `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md`
   as the required citation for any 3D-to-1D thermal comparison.
2. Claim `TODO-PREDICT-COOLER-REMOVAL` before treating the 1D cooler as
   predictive from hardware settings.
3. Claim `TODO-PREDICT-HEATER-FLUID-FRACTION` before treating resistor wattage
   as a predicted fluid heat input.
4. Claim `TODO-1D-RADIATION-CAPABILITY` before making radiation-on 1D
   predictions beyond sensitivity analysis.
5. Add first-class fixed-mdot/frozen-hydraulics support in Fluid before using
   replay rows in formal model-form bakeoff tables.
