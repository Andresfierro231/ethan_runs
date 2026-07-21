# 2026-07-08 Ethan Runs Journal

This curated entry summarizes the Codex-owned July 8 work and points to the raw
agent journals, status files, operational notes, scripts, and work products.
It is intentionally conservative: observed output, interpretation, limitations,
and next steps are separated.

## Coordination Source

Raw closeout:

- `.agent/journal/2026-07-08/codex-day-provenance-closeout.md`

Key status files:

- `.agent/status/2026-07-08_AGENT-202.md`
- `.agent/status/2026-07-08_AGENT-205.md`
- `.agent/status/2026-07-08_AGENT-206.md`
- `.agent/status/2026-07-08_AGENT-207.md`
- `.agent/status/2026-07-08_AGENT-208.md`
- `.agent/status/2026-07-08_AGENT-209.md`
- `.agent/status/2026-07-08_AGENT-211.md`
- `.agent/status/2026-07-08_AGENT-213.md`
- `.agent/status/2026-07-08_AGENT-214.md`
- `.agent/status/2026-07-08_AGENT-215.md`

## Main Outcomes

### CFD Geometry And Boundary Classification

Observed:

- The audited Salt CFD roots use a `0.03556 m` wall/insulation layer
  (`1.4 in`).
- The `0.25 in` / `0.30 in` values are 1D temperature-matching settings, not
  CFD insulation labels.
- The audited CFD cases include emissivity metadata on `rcExternalTemperature`
  patches but no `constant/radiationProperties`, `qr`, or `G` radiation field.

Primary evidence:

- `work_products/2026-07-08_cfd_scenario_contract/**`
- `operational_notes/07-26/08/2026-07-08_cfd_1d_geometry_bc_contract_and_run_plan.md`

Limitation:

- This classification is read-only setup evidence. Mesh/GCI and full
  latest-window requalification remain separate open work.

### Salt 1 Continuation

Observed:

- A corrected Salt 1 nominal continuation candidate was staged under
  `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/**`.
- The copied convergence monitor was changed to diagnostic-only.
- Job `3282992` (`salt1_nom_cont`) was submitted and initially pending by
  priority.

Primary evidence:

- `.agent/status/2026-07-08_AGENT-206.md`
- `operational_notes/07-26/08/2026-07-08_salt1_nominal_continuation_submit.md`

Limitation:

- This is not yet usable closure evidence; it needs a completed run, formal
  gate, and admission/window review.

### Test-Section Heat Contract

Observed:

- The 1D model applies `37 W` gross Salt test-section heat input.
- The CFD Salt 2/3/4 test-section `wallHeatFlux` rows are net sinks.
- The refreshed chart package includes a segment enthalpy-residual figure and
  table.

Primary evidence:

- `operational_notes/07-26/08/2026-07-08_test_section_heat_contract_and_analysis_plan.md`
- `work_products/2026-07-08_postprocessor_summary_charts/**`

Limitation:

- Gross imposed source and net wall heat transfer are not interchangeable.
  Predictive test-section behavior needs the competing quartz/ambient loss path.

### Thermal Boundary Contract

Observed:

- Current CFD Salt thermal contract label:
  `cfd_salt_1p4in_layer_present_surface_emissivity_bc_metadata_present_no_qr_field`.
- Prior 1D state is `61.950-66.201 K` hotter than CFD and has loop Delta T
  `3.722-3.908 K` smaller.

Primary evidence:

- `work_products/2026-07-08_thermal_boundary_contract/**`
- `operational_notes/07-26/08/2026-07-08_thermal_boundary_contract_and_frozen_replay_plan.md`

Limitation:

- Frozen-hydraulics/fixed-mdot replay still needs first-class Fluid solver
  metadata or a reviewed wrapper for paper-grade provenance.

### Thermal Mismatch Deep Dive And Fixed-Mdot Replays

Observed:

- Heater imposed duty exceeds heater `wallHeatFlux` into the fluid:
  Salt 2 `265.700 W` vs `243.519 W`; Salt 3 `297.500 W` vs `273.155 W`;
  Salt 4 `337.600 W` vs `310.487 W`.
- Current 1D cooler removal is about `46-54 W`, while CFD cooler heat removal is
  about `136-169 W`.
- Fixed-mdot replay path `P1_cfd_cooler_duty_only` is the best current thermal
  path; formal background runs report mean absolute Tmean error `4.456 K` and
  mean absolute loop-Delta-T error `0.140 K`.
- No path passes the strict thermal gate.

Primary evidence:

- `.agent/journal/2026-07-08/cfd-informed-fixed-mdot-1d-background-runs.md`
- `.agent/status/2026-07-08_AGENT-211.md`
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/**`
- `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/**`
- `operational_notes/07-26/08/2026-07-08_thermal_mismatch_remedy_deep_dive.md`
- `operational_notes/07-26/08/2026-07-08_cfd_informed_fixed_mdot_1d_runs.md`

Limitation:

- These are CFD-informed thermal replays at fixed CFD mdot. They should not be
  used as fully predictive results from physical resistor wattage and cooling
  hardware settings.
- The final `AGENT-211` run used existing Fluid functions read-only rather than
  a committed first-class `fixed_mdot_kg_s` Fluid solver mode, because
  `AGENT-210` owned the external Fluid solver files.
- Pressure residuals in `fixed_mdot_pressure_replay_results.csv` are diagnostic
  only and must not be treated as predictive hydraulic pass/fail scores.
- The best path, `P1_cfd_cooler_duty_only`, prescribes CFD cooler
  wallHeatFlux. It diagnoses the missing cooler sink but is not yet a
  predictive cooler model.
- The preferred split source/loss sign convention appears in `P5`, but current
  Fluid prescribed-loss semantics zero unlisted passive losses. That row is a
  solver-capability diagnostic, not a closure candidate.
- The full fixed-Q heat-ledger path is under-anchored for absolute mean
  temperature because heat rates do not depend on wall/surface/ambient
  temperature.

AGENT-211 provenance detail:

- Final command:
  `srun -n 1 env PYTHONUNBUFFERED=1 python tools/analyze/run_cfd_informed_fixed_mdot_1d_replays.py --output-dir work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs`
- Final Slurm provenance in `run_metadata.json`: job `3282230`, step `1`, host
  `c318-008.ls6.tacc.utexas.edu`, Python `3.9.7`.
- Direct inputs were
  `case_thermal_targets.csv`, `cfd_thermal_boundary_contract.csv`, the
  patchwise heat ledger, the span endpoint temperature products, the fixed-mdot
  solver plan, and the helper-agent prompts from the thermal mismatch package.
- Read-only Fluid dependencies were `solver.py`, `geometry.py`,
  `config_loader.py`, and `configs/cases.yaml` under
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/`.

### Interface Power Policy

Decision:

- 3D-to-1D CFD-informed comparisons must use realized CFD interface heat rates:
  heater `wallHeatFlux` / `heat_to_fluid_W` for heat input and CFD cooler
  `wallHeatFlux` sink magnitude / `cooler_removed_duty_W` for heat removal.
- Idealized resistor wattage and idealized cooler capacity are future
  predictive targets, not current comparison inputs.
- Current 3D CFD has no separate `qr` radiation heat-loss term; 1D radiation
  should be developed and reported separately without double-counting CFD
  `wallHeatFlux`.

Primary evidence:

- `.agent/DECISIONS.md`
- `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md`
- `.agent/status/2026-07-08_AGENT-213.md`

Future board work:

- `TODO-PREDICT-HEATER-FLUID-FRACTION`
- `TODO-PREDICT-COOLER-REMOVAL`
- `TODO-1D-RADIATION-CAPABILITY`

### Heat Enthalpy Interface Follow-up

Observed:

- The July 8 patchwise heat ledger now contains a first enthalpy-residual layer
  for bracketed spans, using
  `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`.
- That foundation is still not the final physical-interface energy ledger:
  cooler span endpoints bracket only part of the cooler, upcomer endpoints are
  recirculation-contaminated, and junction heat rows are not bracketed by
  enthalpy-flow stations.
- A new unclaimed board row,
  `TODO-HEAT-ENTHALPY-INTERFACE-LEDGER`, was opened for a follow-up package
  under `work_products/<date>_patchwise_heat_ledger_enthalpy_interfaces/**`.

Interpretation:

- The July 8 foundation package should be preserved as provenance. The follow-up
  should rebuild the residual layer using explicit physical segment interfaces,
  patch-to-segment mapping, mdot/cp provenance, recirculation flags, junction
  treatment, sign convention, and `qr` radiation semantics.

Primary evidence:

- `.agent/status/2026-07-08_AGENT-215.md`
- `.agent/journal/2026-07-08/heat-enthalpy-interface-followup-task.md`
- `work_products/2026-07-08_patchwise_heat_ledger/**`
- `work_products/2026-07-08_span_endpoint_temperatures/**`
- `work_products/2026-07-08_thermal_boundary_contract/**`

Limitation:

- `AGENT-215` did not run new extraction or solver work. It opened and
  documented the follow-up task; the future worker must build and validate the
  new package without modifying `work_products/2026-07-08_patchwise_heat_ledger/**`.

## Validation Summary

Recorded successful checks include:

- `AGENT-202`: scenario-contract builder and syntax check passed.
- `AGENT-207`: postprocessor chart builder passed; focused tests passed
  (`3 passed`).
- `AGENT-208`: thermal-boundary builder passed; focused tests passed
  (`5/5`).
- `AGENT-209`: thermal-mismatch builder passed; focused tests passed (`3/3`).
- `AGENT-211`: fixed-mdot replay tests and syntax checks passed; final `srun`
  completed in Slurm job `3282230`, step `1`, and wrote the run package.
- `AGENT-213` and `AGENT-214`: documentation tasks validated with targeted
  `rg` checks for discoverability and policy/provenance terms.
- `AGENT-215`: coordination-only follow-up validated by reading the July 8
  heat-ledger, span-endpoint, and thermal-boundary-contract packages and adding
  a scoped board row plus status/journal handoff.

## Limitations To Preserve In Thesis/Paper Text

- Current thermal replay agreement is CFD-interface-informed, not fully
  predictive from electrical and cooler hardware inputs.
- Heater electrical wattage is not the same as heat entering the fluid.
- Current idealized 1D cooler removal is not the same as the CFD cooler heat
  removed from the fluid.
- Radiation is not represented as a separate current CFD heat-ledger term.
- Corrected Salt perturbations and Salt 1 continuation outputs are not closure
  evidence until formally gated.
- Mesh/GCI and latest-window uncertainty remain open.
- Hydraulic and thermal calibration must remain separated; do not tune friction
  to compensate for a thermal-state mismatch.

## Next Actions

1. Use the thermal-interface policy note before any 3D-to-1D comparison.
2. Build a predictive cooler-removal model and validate it on held-out cases.
3. Build a predictive heater fluid-entry fraction model and validate it on
   held-out cases.
4. Add or verify 1D radiation capability with analytic tests and sensitivity
   tables, while avoiding CFD `wallHeatFlux` double counting.
5. Add first-class fixed-mdot/frozen-hydraulics mode and clearer prescribed
   source/loss semantics to the Fluid solver before formal model-form bakeoff.
6. Claim `TODO-HEAT-ENTHALPY-INTERFACE-LEDGER` to rebuild heat residuals from
   physical segment-interface enthalpy extraction in a new package.

## Claude Literature-Closure Rigor Review

Observed:

- A review of Claude's July 7-8 closure-fit artifacts was added in
  `operational_notes/07-26/08/2026-07-08_claude_literature_closure_fit_rigor_review.md`.
- The review covered `F3_shah_apparent`, `F4_leg_class`, the F4 Ri gate,
  `F5_ri_corrected`, `F6_phi_re`, minor-loss separation, upcomer correlation
  v2, the July 8 model-form context, and the related Fluid implementation paths.

Interpretation:

- Claude's work is acceptable as diagnostic post-processing, candidate-screen
  development, prototype implementation, and negative-result documentation.
- It is not yet acceptable as final publication-grade closure-law evidence.
- `F3_shah_apparent` is the strongest current friction baseline.
- `F5_ri_corrected` should be treated as a negative-result scaffold because its
  active Ri coefficients are zeroed and it behaves like F3.
- `F4_leg_class`, `F6_phi_re`, and the upcomer fit must remain training-set or
  candidate-screen artifacts until they pass corrected-run admission, held-out
  validation, thermal-state replay, and uncertainty checks.
- The minor-loss separation package is only a sensitivity study at present,
  because it contains a span/corner control-volume contradiction.

Primary evidence:

- `.agent/status/2026-07-08_AGENT-216.md`
- `.agent/journal/2026-07-08/claude-literature-closure-fit-rigor-review.md`
- `operational_notes/07-26/08/2026-07-08_claude_literature_closure_fit_rigor_review.md`

Limitation:

- `AGENT-216` was a review/documentation task. It did not rerun the closure
  fits, edit Fluid source, alter generated work products, or mutate CFD solver
  outputs.

## Overnight Rigor Studies Setup

Observed:

- `AGENT-218` triaged which rigor-strengthening studies can run overnight.
- Already running overnight-capable CFD jobs:
  - Salt1 nominal continuation `3282992`.
  - Corrected Salt Q jobs `3275448`, `3275449`, and `3275560`.
- Already scheduled gate:
  - `3280969` `saltq_gate_after`, pending on
    `afterany:3275448,3275449,3275560`.
- A bounded overnight monitor/replay script was staged at
  `work_products/2026-07-08_overnight_rigor_studies_setup/run_overnight_rigor_studies.sbatch`,
  but TACC rejected submission because queued/running project jobs already
  encumber more SUs than the current account balance.

Immediate lightweight results:

- Corrected Salt preflight audit: `14` cases audited, `0` failures.
- Corrected Salt live monitor: `14` cases scanned, `4` special-scrutiny flags.
- Flagged rows: Salt1 low/high corrected-Q hold for coordinator review; Salt1
  high ended early; Salt3 high-5/high-10 require log-marker investigation.

Interpretation:

- The best overnight value is to let existing CFD jobs and the already queued
  formal gate proceed.
- No duplicate Salt1 or corrected Salt CFD should be launched.
- Full mesh/GCI, minor-loss coefficient correction, held-out bakeoff, and Ri
  validation should be staged as follow-up tasks rather than launched blindly.

Primary evidence:

- `.agent/status/2026-07-08_AGENT-218.md`
- `.agent/journal/2026-07-08/overnight-rigor-studies-setup.md`
- `operational_notes/07-26/08/2026-07-08_overnight_rigor_studies_setup.md`
- `work_products/2026-07-08_overnight_rigor_studies_setup/**`

## Final Closeout For Tomorrow Pickup

User request:

- The user is closing for today and asked that the presentation package and
  current context be documented in today's journal before tomorrow's pickup.

Observed:

- `AGENT-219` completed a presentation package at
  `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/**`.
- The package expands the July 8 postprocessor story into a 12-slide outline
  with slide titles, bullets, figure calls, and speaker notes:
  `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md`.
- The package includes a missing/nice-to-have figure inventory:
  `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/missing_and_nice_to_have_figures.md`.
- `AGENT-219` created four reusable-script support figures:
  - `figures/minor_loss_k_apparent_vs_local.svg`
  - `figures/minor_loss_separation_phi.svg`
  - `figures/fixed_mdot_thermal_replay_error.svg`
  - `figures/t13_re_sweep_plan.svg`
- The reusable builder and tests are:
  - `tools/analyze/build_tomorrow_presentation_package.py`
  - `tools/analyze/test_tomorrow_presentation_package.py`
- Validation passed:
  - `python -m py_compile tools/analyze/build_tomorrow_presentation_package.py tools/analyze/test_tomorrow_presentation_package.py`
  - `python tools/analyze/build_tomorrow_presentation_package.py`
  - `python -m pytest tools/analyze/test_tomorrow_presentation_package.py -q`
  - focused result: `3 passed in 0.35s`.

Interpretation:

- Tomorrow's presentation is ready as a decomposed-evidence story, not as a
  final closure-coefficient claim.
- The main deck should use the original postprocessor summary figures for:
  pressure decomposition, heat accounting, heat residuals, friction-form mdot
  screen, F5/Ri screen, upcomer backflow, and corrected-Salt status.
- The four new AGENT-219 figures should be used as support or backup slides for
  questions on minor losses, fixed-mdot thermal replay, and the T13 campaign
  plan.
- The central message should remain: the CFD evidence has been decomposed into
  pressure, heat, and regime terms with provenance, residuals, and admission
  boundaries; this is the right foundation for a predictive 1D model.

Preserve these claim boundaries:

- Do not claim publication-grade closure coefficients yet.
- Do not use corrected Salt perturbations as closure-fit evidence until the
  formal gate admits them.
- Do not present the fixed-mdot replay as a predictive hydraulic solution; it is
  a thermal-boundary diagnostic.
- Do not promote `K_local` as final minor-loss truth; the current two-tap rows
  still lack full centerline tap-to-tap lengths for preserved features and raw
  extraction for the test-section complex.
- Do not invent mesh/GCI or time-window uncertainty figures; those packages
  still need to be run.

Tomorrow pickup checklist:

1. Open
   `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md`.
2. Check the scheduler/gate state before interpreting any new run outputs:
   Salt1 nominal continuation, corrected Salt Q jobs, and corrected-Salt gate.
3. If deck polish is needed, work from the package README, `figure_manifest.csv`,
   and `source_inventory.csv`; regenerate with
   `python tools/analyze/build_tomorrow_presentation_package.py` rather than
   hand-editing generated figures.
4. Assign bounded follow-up rows for the remaining rigor work:
   mesh/GCI uncertainty, time-window uncertainty, raw feature two-tap extraction,
   station-resolved development analysis, detailed upcomer invalidity metrics,
   and predictive heater/cooler boundary models.
5. Use the final closeout status and raw handoff for traceability:
   - `.agent/status/2026-07-08_AGENT-221.md`
   - `.agent/journal/2026-07-08/final-user-closeout-and-tomorrow-pickup.md`
