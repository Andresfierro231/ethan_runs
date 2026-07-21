# Codex End-of-Day CFD Closure Handoff

Date: `2026-07-07T20:00:14-05:00`
Role: Coordinator / Writer
Task ID: `AGENT-181` handoff journal extension
Owner: codex
Worktree: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

## Purpose

This journal is written at user request before leaving for the day. It is meant
to let a fresh session tomorrow reconstruct the state of the CFD-to-1D closure
work without relying on chat history.

The main user directive at end of day was:

- some of the friction and hydraulic closure analyses done today, especially
  the Claude-generated per-leg/F4/F5 work, may be poorly posed;
- the desired study is not just a per-leg multiplier fit;
- the desired study should distinguish:
  - hydrodynamic development pressure drop;
  - thermal / mixed-convection development pressure drop;
  - minor-loss pressure drop;
  - developing major losses informed by literature model forms;
- the 1D validation should use the actual CFD setup, including the expected
  `1.4 in` CFD insulation and radiative losses if those are present in the CFD;
- the goal is to derive physically interpretable model forms from CFD and test
  whether the 1D model with those forms can match CFD.

Codex assessment: the current artifacts are useful diagnostics but are not yet
a scientifically rigorous closure study. The next session should build an
observation-to-closure contract before touching more 1D coefficients.

## Startup / Coordination Context

Required startup files were read earlier in the session and again for this
handoff:

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/journal/README.md`
- `.agent/status/2026-07-07_AGENT-181.md`

Relevant board state at handoff:

- `AGENT-181` is codex-owned and includes this journal path in scope:
  `.agent/journal/2026-07-07/codex-end-of-day-cfd-handoff.md`.
- `AGENT-200` is complete and generated the F5 Ri-corrected candidate screen.
- `AGENT-199` is complete and fixed F4 stub segment mapping in the external
  Fluid solver.
- `AGENT-197` is complete and fixed the pressure-ledger entry/development flag.
- Retired but relevant rows include `AGENT-193` through `AGENT-196`, especially
  pressure ledger, heat ledger, friction mdot comparison, and upcomer correlation.

This handoff only creates a journal file. It does not mutate solver outputs,
case trees, or external Fluid code.

## Files Changed In This Handoff

- `.agent/journal/2026-07-07/codex-end-of-day-cfd-handoff.md`

No code, case data, generated model outputs, or Slurm submissions were changed
by this handoff.

## Commands Run For Status / Handoff Context

Representative commands run today by Codex for this handoff and the preceding
status check:

```bash
pwd
cat AGENTS.md
cat .agent/BOARD.md
cat .agent/FILE_OWNERSHIP.md
cat .agent/ROLES.md
cat .agent/journal/README.md
cat .agent/status/2026-07-07_AGENT-181.md
cat .agent/status/2026-07-07_AGENT-195.md
cat .agent/status/2026-07-07_AGENT-196.md
cat .agent/status/2026-07-07_AGENT-200.md
sed -n '1,260p' operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md
sed -n '1,220p' work_products/2026-07-07_pressure_term_ledger/README.md
sed -n '1,220p' work_products/2026-07-07_f4_ri_calibration_and_solver_gate/README.md
sed -n '1,220p' work_products/2026-07-07_friction_forms_comparison/README.md
sed -n '1,220p' work_products/2026-07-07_heat_source_sink_ledger/README.md
sed -n '1,260p' work_products/2026-07-07_f5_ri_corrected/README.md
tail -80 work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_gap_local.log
tail -80 tmp/2026-07-06_overnight_postprocess_jobs/slurm-jin_gap_rerun-3278454.out
tail -80 tmp/2026-07-06_overnight_postprocess_jobs/slurm-jin_gap_rerun-3278454.err
sacct -j 3278454 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End
ps -f -p 94224
ps -f -p 88711
squeue -u $USER
date -Iseconds
```

The failed `cat .agent/status/2026-07-07_AGENT-200.md` seen earlier in the
session was stale at that moment. By this handoff, the file exists and was read.

## Key Files To Read Tomorrow First

Start with these files in this order.

1. Coordination and current task state:
   - `.agent/BOARD.md`
   - `.agent/status/2026-07-07_AGENT-181.md`
   - `.agent/journal/2026-07-07/water-provisional-and-corrected-salt-gate.md`
   - this file: `.agent/journal/2026-07-07/codex-end-of-day-cfd-handoff.md`

2. Scientific guardrail / best current critique:
   - `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`

3. Existing pressure / hydraulic artifacts:
   - `work_products/2026-07-07_pressure_term_ledger/README.md`
   - `work_products/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv`
   - `work_products/2026-07-07_pressure_term_ledger/summary.json`
   - `.agent/journal/2026-07-07/implementer-pressure-term-ledger.md`
   - `.agent/journal/2026-07-07/implementer-pressure-ledger-entry-fix.md`

4. Existing friction-form artifacts:
   - `work_products/2026-07-07_friction_forms_comparison/README.md`
   - `work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv`
   - `work_products/2026-07-07_friction_forms_comparison/summary.json`
   - `.agent/status/2026-07-07_AGENT-195.md`
   - `.agent/journal/2026-07-07/implementer-friction-mdot-comparison.md`

5. Existing F4 / Ri / F5 artifacts:
   - `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/README.md`
   - `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.csv`
   - `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/ri_definition_audit.md`
   - `work_products/2026-07-07_f5_ri_corrected/README.md`
   - `work_products/2026-07-07_f5_ri_corrected/f5_fit_summary.csv`
   - `work_products/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv`
   - `.agent/status/2026-07-07_AGENT-200.md`
   - `.agent/journal/2026-07-07/implementer-f5-ri-corrected.md`

6. Existing heat / thermal artifacts:
   - `work_products/2026-07-07_heat_source_sink_ledger/README.md`
   - `work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv`
   - `.agent/status/2026-07-07_AGENT-194.md`
   - `.agent/journal/2026-07-07/implementer-heat-source-sink-ledger.md`

7. Existing upcomer recirculation artifacts:
   - `work_products/2026-07-07_upcomer_correlation_v2/README.md`
   - `work_products/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv`
   - `.agent/status/2026-07-07_AGENT-196.md`
   - `.agent/journal/2026-07-07/implementer-upcomer-correlation.md`

8. Background per-leg gap analysis outputs:
   - `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_gap_local.log`
   - `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/jin_insulation_sweep.csv`
   - `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/matched_closure_compare_jin.csv`
   - `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/perleg_segment_dp_jin.csv`
   - `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/f_re_fit_perleg.csv`
   - `.agent/journal/2026-07-07/implementer-jin-gap-api-refresh.md`

9. Corrected Salt gate / run-admission state:
   - `work_products/2026-07-07_corrected_salt_live_monitor/README.md`
   - `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`
   - `work_products/2026-07-07_corrected_salt_live_monitor/overnight_decision_snapshot_2026-07-07/OVERNIGHT_SUBMIT_README.md`
   - `work_products/2026-07-07_corrected_salt_live_monitor/overnight_decision_snapshot_2026-07-07/salt1_coordinator_review.md`
   - `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/README.md`

## What Completed Today

### Background per-leg gap analysis

The background/local `jin_perleg_gap` run completed successfully after earlier
API fixes.

Evidence:

- `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_gap_local.log`
  ends with `All steps complete.`
- Recorded background PIDs checked by Codex:
  - `94224`: no longer running;
  - `88711`: no longer running.
- Slurm rerun `3278454` failed quickly, but that was the earlier stale-API
  attempt, not the later successful local/background rerun.

Slurm failure details for `3278454`:

- `sacct`: `FAILED`, exit `1:0`, elapsed `00:00:04`;
- stderr: `TypeError: __init__() got an unexpected keyword argument 'use_radiation'`.

Successful local/background run results:

- matched insulation from the diagnostic sweep:
  - Salt 2: about `0.25 in`;
  - Salt 3: about `0.30 in`;
  - Salt 4: about `0.30 in`;
- default/F1 mdot errors at those matched temperatures:
  - Salt 2: `+9.7%`;
  - Salt 3: `+16.2%`;
  - Salt 4: `+18.0%`;
- per-leg/global multiplier runs often swung too far negative, roughly
  `-16%` to `-24%` depending case and form.

Critical interpretation: these matched-insulation values are diagnostic only.
They are not the physical CFD setup if the actual CFD insulation is supposed
to be `1.4 in`.

### Friction form mdot comparison, AGENT-195

Output:

- `work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv`
- `work_products/2026-07-07_friction_forms_comparison/README.md`
- `work_products/2026-07-07_friction_forms_comparison/summary.json`

Reported mdot error table:

| Form | Salt 2 | Salt 3 | Salt 4 |
| --- | ---: | ---: | ---: |
| `F1` | `+9.70%` | `+16.21%` | `+17.97%` |
| `F3_hagenbach` | `+3.50%` | `+6.69%` | `+5.69%` |
| `F3_shah_apparent` | `-0.93%` | `+3.33%` | `+3.75%` |
| `F4_leg_class` | `-23.19%` | `-23.57%` | `-24.66%` |

Important caveats:

- minor losses were set to zero in this comparison;
- comparison used the diagnostic temperature-matched insulation values above,
  not the expected actual CFD `1.4 in` insulation;
- per-leg pressure drops in the CSV are distributed friction only, not a full
  ledger of hydrodynamic development, thermal development, local feature loss,
  and residual;
- `F4_leg_class` over-stiffens the 1D loop and should not be treated as a
  validated hydraulic law.

### F5 Ri-corrected candidate, AGENT-200

Output:

- `work_products/2026-07-07_f5_ri_corrected/README.md`
- `work_products/2026-07-07_f5_ri_corrected/f5_fit_summary.csv`
- `work_products/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv`
- `work_products/2026-07-07_f5_ri_corrected/summary.json`
- `.agent/status/2026-07-07_AGENT-200.md`
- `.agent/journal/2026-07-07/implementer-f5-ri-corrected.md`

Fit result:

| leg_class | n | c_fitted | R2 | c_active | interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| heater | 3 | `1.473` | `-74.57` | `0.0` | poor, set to no correction |
| cooler | 3 | `0.608` | `-27.50` | `0.0` | poor, set to no correction |
| downcomer | 3 | `0.721` | `-4.30` | `0.0` | poor, set to no correction |
| upcomer | 0 | `NA` | `NA` | `0.0` | excluded due to recirculation |

Because all active coefficients are zero, `F5_ri_corrected` is numerically
identical to `F3_shah_apparent` for the current data:

- Salt 2: `-0.93%`;
- Salt 3: `+3.33%`;
- Salt 4: `+3.75%`.

Critical interpretation: F5 is framework plumbing and a failed 3-point screen,
not a scientific Ri closure. The current OLS target and evidence set are not
adequate for a portable mixed-convection friction law.

### Pressure term ledger, AGENT-193 and AGENT-197

Output:

- `work_products/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07-07_pressure_term_ledger/README.md`

Important findings from README:

- rows: `18` mainline Salt 2/3/4 Jin rows, six spans per case;
- max budget residual before added development/minor terms was small;
- development loss from Shah-F1 proxy can be `20-40%` of distributed friction
  for short entry segments;
- bend/minor loss estimates are only upper bounds;
- recirculation spans are diagnostic only.

AGENT-197 fixed a specific physical issue:

- `test_section_span` and `left_upper_leg` are not fresh entry spans;
- their `development_loss_pa` is now `0.0`;
- `flow_reset_flag` was added to distinguish fresh-entry vs inherited-developed
  flow.

Critical interpretation: this ledger is closer to the right direction, but it
still does not fully extract station-based total pressure, two-tap minor loss,
thermal-development pressure, or literature-informed developing major-loss
terms. It should be treated as a predecessor to a better ledger, not the final
closure input.

### Heat source/sink ledger, AGENT-194

Output:

- `work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv`
- `work_products/2026-07-07_heat_source_sink_ledger/README.md`

Important findings:

- per-patch-group wallHeatFlux integrals were assembled for Salt 2/3/4 Jin;
- test section net inner-wall heat flux is negative in all three cases despite
  intended electrical input;
- enthalpy change per span is not available yet because inlet/outlet bulk
  temperatures per span were not extracted;
- resistance network decomposition is not done;
- README states `radiation_present = False` for all rows.

Critical interpretation: this is a boundary-flux ledger, not yet a thermal
driver ledger. If the intended CFD setup has radiative losses and `1.4 in`
insulation, tomorrow must audit whether these analyzed rows are the right cases
or whether radiation extraction/setup is missing.

### Upcomer correlation, AGENT-196

Output:

- `work_products/2026-07-07_upcomer_correlation_v2/README.md`
- `work_products/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv`
- `.agent/status/2026-07-07_AGENT-196.md`

Fit:

```text
bf = a + b/Re
a = 0.05389
b = 15.931
```

Dataset:

| case | Re | backflow fraction | Ri_median | Nu |
| --- | ---: | ---: | ---: | ---: |
| salt_2_jin | `71.1` | `0.278` | `2.634` | `3.107` |
| salt_3_jin | `96.8` | `0.219` | `2.396` | `4.060` |
| salt_4_jin | `134.9` | `0.172` | `1.498` | `4.986` |

Critical interpretation: this confirms the upcomer is not ordinary
single-stream pipe friction. Upcomer rows should not be blindly fit as Darcy
friction coefficients. They need an onset/regime treatment or exclusion from
single-stream closure fitting.

## User Critique Captured At End Of Day

The user explicitly questioned the current Claude friction/hydraulic closure
work and requested a more scientific redo.

User's desired decomposition:

1. per-leg friction models;
2. hydrodynamic development separated from fully developed friction;
3. thermal-development / mixed-convection pressure drop separated from
   hydrodynamic development;
4. minor losses separated from major losses;
5. developing major losses informed by literature model forms;
6. 1D validation against the actual CFD setup, including the expected
   `1.4 in` insulation and radiative losses;
7. model forms derived from CFD and tested for whether the 1D model can match
   CFD.

Codex agrees that the current state falls short. The main reason is not just
bad coefficients; it is that the target being fit is not yet cleanly defined.

## Scientific Assessment: What Is Missing

### 1. Actual CFD scenario contract

The current comparisons use diagnostic "matched insulation" values:

- Salt 2: `0.25 in`;
- Salt 3: `0.30 in`;
- Salt 4: `0.30 in`.

This was done to match loop temperature in the 1D model. It is not physically
equivalent to validating the 1D model against the CFD case if the CFD setup
should have `1.4 in` insulation.

Tomorrow must audit:

- which CFD case roots correspond to the intended `1.4 in` insulation setup;
- whether the CFD actually includes radiation;
- whether OpenFOAM outputs include radiation terms such as `qr`, radiation
  model dictionaries, or radiative wall heat-flux components;
- whether the current Salt 2/3/4 Jin mainline continuations are the correct
  cases for the user's intended comparison.

### 2. Pressure balance must be station-based, not only span-average

The next pressure ledger should use station-to-station quantities, not only
span-level average gradients.

Minimum quantities per station:

- `p_rgh`;
- reconstructed static pressure if possible;
- density;
- velocity / bulk velocity vector;
- dynamic head `0.5*rho*u^2`;
- total pressure proxy `p + 0.5*rho*u^2`;
- station area / hydraulic diameter;
- flow direction and gravity projection;
- wall temperature / bulk temperature;
- wall heat flux;
- Re, Pr, Gr/Ra/Ri;
- source path, field time, time window, extraction method, and quality flags.

Minimum station-pair terms:

```text
observed pressure behavior
  = reversible buoyancy head
  + acceleration / dynamic-pressure change
  + fully developed major loss
  + hydrodynamic development excess
  + thermal / mixed-convection major-loss correction
  + local minor loss
  + recirculation / invalid-single-stream contribution
  + residual
```

No new friction closure should be fit until this decomposition exists.

### 3. Hydrodynamic development and thermal development are being conflated

`F3_shah_apparent` is a hydrodynamic developing laminar flow model. It does not
by itself represent:

- buoyancy-distorted velocity profiles;
- wall heating/cooling mixed convection;
- density/viscosity stratification;
- recirculation cells;
- local feature losses.

Tomorrow's model form should look more like:

```text
DeltaP_major =
  DeltaP_fd_laminar(Re, L/D)
  + DeltaP_hydro_development(Re, x+)
  + DeltaP_thermal_mixed_convection(Re, Pr, Gr, Ri, heating/cooling sign, orientation)
```

or equivalently:

```text
f_effective =
  (64/Re)
  * Phi_hydro(x+)
  * Phi_thermal(Ri, Gr/Re^2, Pr, sign(q"), orientation)
```

but only after feature/minor losses and reversible buoyancy have been separated.

### 4. Minor losses need two-tap total-pressure extraction

Current bend/minor loss rows are upper bounds. A rigorous method should:

1. define two taps around each bend, reducer, junction, and transition;
2. compute total pressure proxy at upstream/downstream taps;
3. subtract adjacent straight distributed major loss over the tap distance;
4. normalize by local bulk dynamic pressure;
5. emit both:
   - `K_local`: corrected local feature loss;
   - `K_apparent`: uncorrected diagnostic feature loss;
6. join each row to the pressure ledger by case, feature, station IDs, time
   window, and provenance.

There is already a planned queue item:

- `TODO-MINOR-LOSS-TWO-TAP`

That queue row is a good starting point, but it should be coordinated with the
more general observation-table contract.

### 5. Thermal driver mismatch blocks mdot-only validation

The deep-dive note records a major caveat from earlier 1D work: under one
nominal scenario with per-leg CFD friction multipliers, the 1D loop was roughly
`62-66 K` hotter than CFD.

Consequences:

- mdot error cannot be assigned purely to hydraulic friction;
- viscosity, density, buoyancy head, Re, and thermal losses are all affected;
- a closure that matches mdot while missing temperature is not validated;
- a closure that misses mdot while the thermal state is wrong is not necessarily
  hydraulically wrong.

Tomorrow's validation target must compare:

- mdot;
- loop mean temperature;
- leg inlet/outlet bulk temperatures;
- per-leg pressure terms;
- heat-source/sink ledger;
- radiation and insulation consistency.

### 6. Upcomer needs a regime model

The upcomer has documented backflow / recirculation. It should not be treated
as ordinary pipe friction unless a regime criterion says single-stream pipe
friction is valid.

Use or reopen:

- `TODO-UPCOMER-ONSET`
- `work_products/2026-07-07_upcomer_correlation_v2/**`

Recommended treatment:

- classify upcomer rows as ordinary single-stream, recirculation-diagnostic, or
  excluded from friction fitting;
- if included, use a separate onset / two-region model rather than a scalar
  Darcy multiplier.

### 7. Evidence set is too small for portable correlations

Only Salt 2/3/4 Jin are admitted for current fitting. This is three operating
points over a narrow Re/Ri range. It can support:

- decomposition checks;
- model-form screening;
- consistency tests;
- diagnostic comparisons.

It cannot support:

- portable Ri correlations;
- broad per-leg laws;
- train/validation claims without more admitted points.

Corrected Q perturbations are not yet admissible. See the AGENT-181 corrected
Salt gate notes.

## Proposed Scientific Redo Plan

### Phase 0: freeze the real scenario contract

Open a Coordinator/Writer or Implementer task to audit the actual CFD setup.

Deliverables:

- `work_products/<date>_cfd_scenario_contract/`
- table with one row per CFD case:
  - case root;
  - source ID;
  - mesh level;
  - continuation status;
  - time window;
  - insulation thickness;
  - wall material / thickness;
  - radiation model present/absent;
  - heater power;
  - cooler BC;
  - ambient BC;
  - property model;
  - convergence/gate verdict;
  - closure-fit admissibility;
  - validation-use admissibility.

Acceptance criteria:

- explicitly answer whether the cases being analyzed are the intended
  `1.4 in + radiation` CFD cases;
- if not, identify the correct case roots or mark the study blocked.

### Phase 1: canonical closure observation table

Claim or refine:

- `TODO-OBSERVATION-TABLE-CONTRACT`

Deliverable:

- `closure_observations.csv`

One row should be one observable, not one coefficient. Example row types:

- pressure station;
- pressure station pair;
- feature two-tap loss;
- leg bulk enthalpy change;
- patch wall heat flux;
- mdot;
- recirculation metric;
- thermal boundary metric.

Required columns:

- `source_id`, `case_root`, `run_class`, `mesh_level`;
- `time_window_start_s`, `time_window_end_s`;
- `observable_type`, `span`, `feature_id`, `station_start`, `station_end`;
- `value`, `units`, `method`, `source_path`;
- `fit_eligible`, `validation_eligible`, `exclusion_reason`;
- `quality_flags`, `gate_verdict`, `needs_special_gate_scrutiny`.

This table should become the only input to closure fitting and model-form
bakeoff.

### Phase 2: station pressure ledger

Claim or supersede:

- `TODO-PRESSURE-TERM-LEDGER`

But improve the acceptance criteria beyond the current AGENT-193 product:

- include station-level p, p_rgh, dynamic head, total pressure proxy;
- explicitly subtract acceleration/dynamic term;
- explicitly compute density-gradient buoyancy term;
- carry flow direction and gravity projection;
- track hydrodynamic development state/reset;
- do not assign residual to thermal development until minor losses and feature
  losses have been handled;
- keep recirculation rows diagnostic.

Expected output:

- `station_pressure_ledger.csv`
- `span_pressure_decomposition.csv`
- `pressure_decomposition_summary.md`

### Phase 3: two-tap minor loss package

Claim:

- `TODO-MINOR-LOSS-TWO-TAP`

Required outputs:

- `feature_minor_losses.csv`
- `feature_tap_definitions.csv`
- `minor_loss_method.md`

Rows should include:

- upstream/downstream total pressure proxy;
- adjacent straight major loss subtraction;
- K based on local dynamic pressure;
- uncertainty / tap-spacing flags;
- feature type: bend, reducer, junction, contraction/expansion, stub.

### Phase 4: thermal heat ledger with enthalpy and radiation

Claim:

- `TODO-PATCHWISE-HEAT-LEDGER`

But ensure it includes:

- span inlet/outlet bulk temperatures;
- enthalpy-flow change `mdot * cp * DeltaT`;
- patchwise wallHeatFlux by physical role;
- radiation terms if present;
- external convection / ambient loss terms where possible;
- residual energy balance;
- insulation/radiation provenance.

This is required before mdot can be used as hydraulic validation.

### Phase 5: literature model-form screening

Claim:

- `TODO-TARGETED-LITREV-FORMS`

Do not implement formulas unless constants and domains are verified from
primary sources or clearly cited secondary sources.

Candidate categories:

- hydrodynamic developing laminar pipe/duct friction:
  - Shah apparent friction;
  - Hagenbach entrance correction;
  - developing laminar duct correlations;
- mixed-convection / buoyancy-modified laminar friction:
  - Ri / Gr/Re^2 modifiers;
  - heating vs cooling sign;
  - vertical vs inclined vs horizontal orientation;
  - stable vs unstable stratification;
- local feature losses:
  - laminar bend K;
  - reducer/contraction/expansion K;
  - junction/box loss diagnostics;
- upcomer recirculation:
  - onset / regime criteria;
  - backflow fraction model;
  - exclusion boundary for single-stream friction.

Each model form should state:

- equation;
- variables;
- validity range;
- expected sign;
- whether it targets irreversible loss only;
- whether it risks buoyancy double counting;
- which observations it can fit.

### Phase 6: model-form bakeoff, then 1D validation

Only after Phases 0-5 should the 1D model be used for validation.

Claim:

- `TODO-MODEL-FORM-BAKEOFF`

But make sure it tests against the actual CFD setup:

- `1.4 in` insulation if that is the CFD setup;
- radiation on if CFD has radiation;
- actual heater/cooler/ambient BCs;
- same property model assumptions as the CFD reference where practical.

Compare:

- mdot;
- loop mean T;
- leg inlet/outlet T;
- per-leg pressure decomposition;
- feature minor losses;
- heat balance;
- recirculation/upcomer regime classification.

Scoring should separate:

- pressure-distribution score;
- mdot score;
- thermal-state score;
- heat-balance score;
- complexity / overfit score;
- fit vs validation separation.

## Recommended Tomorrow Task Order

1. Open a new board row for the scenario contract audit, or fold it into
   `TODO-OBSERVATION-TABLE-CONTRACT` if the coordinator prefers.
2. Confirm or refute the `1.4 in + radiation` CFD setup:
   - inspect relevant case `constant/`, `system/`, `0/T`, radiation dictionaries,
     and wall BCs;
   - inspect whether postProcessing contains radiation outputs.
3. Do not run more F4/F5 coefficient fitting until the scenario contract and
   observation table exist.
4. Build or update the observation table contract.
5. Then improve pressure, minor-loss, and heat ledgers as separate, joinable
   artifacts.
6. Only then do model-form bakeoff and 1D validation.

## Concrete Questions Tomorrow Should Answer

1. Are the Salt 2/3/4 Jin continuations used today actually the cases with
   `1.4 in` insulation?
2. Does the CFD include radiation, or is the current heat ledger correct that
   `radiation_present=False`?
3. If radiation is present, where is it represented in OpenFOAM outputs and
   how should it be included in the heat ledger?
4. What is the exact 1D `ScenarioConfig` that corresponds to each CFD case?
5. Can station-level pressure and temperature be extracted at all leg endpoints
   and feature taps from the retained time windows?
6. Can minor losses be measured by two-tap total pressure rather than inferred
   as upper bounds?
7. Which spans are single-stream fit-eligible, and which are recirculation or
   feature-dominated diagnostics?
8. Which terms are already represented in the 1D solver, especially buoyancy,
   dynamic pressure, test-section transition losses, ambient heat loss, and
   radiation?
9. What is the train/validation split once corrected Salt Q perturbations are
   requalified, if they are requalified?

## Current Interpretation Boundaries

These are the safe statements as of this handoff:

- `F3_shah_apparent` performs best in the current diagnostic mdot comparison,
  but the comparison used temperature-matched insulation and zero minor losses,
  so it is not a final validation.
- `F4_leg_class` and `F5_ri_corrected` should be treated as diagnostic screens,
  not production closures.
- The current F5/Ri screen failed: all non-upcomer leg classes had negative R2
  and active coefficients were set to zero.
- Current pressure-ledger development and minor-loss terms are not yet a full
  closure-grade decomposition.
- Current heat ledger lacks span enthalpy changes and says radiation is absent.
  This conflicts with the user's expectation if the target CFD includes
  radiative losses.
- Upcomer rows are not ordinary single-stream pipe friction because of
  recirculation/backflow.
- No corrected Salt Q perturbation rows are closure-fit admissible yet.
- Salt 1 remains special-scrutiny / non-admissible without separate
  qualification.

## Do Not Do Tomorrow

- Do not silently use the `0.25 in` / `0.30 in` temperature-matched insulation
  as the validation setup if the intended CFD setup is `1.4 in`.
- Do not fit another scalar per-leg multiplier and call it a closure.
- Do not use raw `p_rgh` slopes as friction without buoyancy and acceleration
  decomposition.
- Do not include upcomer recirculation rows in a single-stream friction fit
  without a regime flag and explicit justification.
- Do not admit corrected perturbation rows until AGENT-181 gate conditions are
  satisfied.
- Do not mutate native solver outputs or old invalid perturbation case trees.

## Suggested Board Row To Add Tomorrow

If the coordinator wants a new explicit row, use something like:

```text
TODO-CFD-SCENARIO-CONTRACT
Priority: HIGH
Role: Coordinator / Implementer / Writer
Owner: open
Allowed edit paths:
  .agent/BOARD.md (own row only),
  .agent/status/<date>_TODO-CFD-SCENARIO-CONTRACT.md,
  .agent/journal/<date>/cfd-scenario-contract.md,
  tools/analyze/build_cfd_scenario_contract.py,
  tools/analyze/test_build_cfd_scenario_contract.py,
  work_products/<date>_cfd_scenario_contract/**
Required read-only context:
  Salt 2/3/4 Jin continuation case roots,
  corrected Salt gate outputs,
  heat source/sink ledger,
  pressure term ledger,
  Fluid ScenarioConfig/campaign configs,
  CFD postprocessing closure rigor deep-dive note.
Objective:
  Establish the exact CFD-to-1D scenario contract before further closure fitting:
  insulation, radiation, heater/cooler/ambient BCs, material properties,
  time windows, convergence/admission flags, and corresponding 1D ScenarioConfig
  fields. Explicitly answer whether the current analyzed cases are the intended
  1.4 in + radiation CFD cases.
```

## End State

The workspace is in a useful but scientifically fragile state. The raw material
for a good closure study exists: pressure budget artifacts, heat flux artifacts,
minor-loss screens, per-leg/friction comparisons, upcomer recirculation metrics,
and corrected perturbation staging. The missing layer is the rigorous
observation contract and physical decomposition that prevents the 1D closures
from absorbing thermal setup error, buoyancy double counting, feature losses,
and recirculation into one opaque fitted multiplier.

Tomorrow should begin by proving the CFD scenario contract, especially the
`1.4 in` insulation and radiation question, before any more coefficient fitting.
