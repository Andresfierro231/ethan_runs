# CFD / 1D Geometry-BC Contract And Run Plan

Date: `2026-07-08`
Task: `AGENT-205`
Role: Coordinator / Writer
Status: authoritative checkpoint for current Salt-family interpretation

## Purpose

This note fixes the labels and source hierarchy for comparing the Ethan CFD
Salt runs to the TAMU 1D model. It also records the current corrected-Q run
state so future submissions do not repeat already-running cases.

Use this note with:

- `work_products/2026-07-08_cfd_scenario_contract/scenario_contract.csv`
- `work_products/2026-07-08_cfd_scenario_contract/latest_window_audit.csv`
- `work_products/2026-07-08_cfd_scenario_contract/closure_observations_seed.csv`
- `operational_notes/07-26/08/2026-07-08_ri_characteristic_length_audit.md`

## Source Hierarchy

For CFD setup labels, prefer the case files over campaign prose:

1. `0/T` boundary dictionaries in the staged or continuation case root.
2. `system/functions` for dimensionless diagnostic definitions.
3. `case_config.yaml` only as staging metadata; do not let it override the
   actual `0/T` patch definitions.
4. `scenario_contract.csv` for current audited labels and latest retained
   times.

For 1D setup labels, prefer the tracked Fluid repo files:

1. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/geometry.py`
2. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
3. `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`
4. `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/scenarios.yaml`
5. `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/campaigns.yaml`

## CFD Geometry / BC Contract

Current audited Salt CFD case roots use this label:

`1.4in_layer_present__surface_emissivity_bc_present_no_volume_radiation_field`

This is intentionally specific. The `0/T` files contain a `0.03556 m` layer,
which is `1.4 in`, and audited Salt mainline/corrected roots carry
`rcExternalTemperature` patches with emissivity metadata. The same audit found
no `constant/radiationProperties`, `qr`, or `G` fields, so the safest radiation
label is not `radiation absent`; it is surface-emissivity metadata present in
the wall boundary condition with no detected OpenFOAM volume-radiation field.

Do not label the CFD as `0.25 in` or `0.30 in`. Those values are 1D diagnostic
temperature-matching sweep settings seen in prior closure comparisons, not the
actual CFD wall/insulation setup.

Patch roles to preserve in downstream tables:

| Role | CFD patch family | Contract note |
| --- | --- | --- |
| Lower heater | `pipeleg_lower_04_straight`, `pipeleg_lower_05_straight`, `pipeleg_lower_06_straight` | Salt heater power distributed over three lower-leg patches. |
| Quartz test-section input | `pipeleg_left_04_test_section` | Separate `37 W` source; bare quartz/test-section behavior must not be collapsed into main-pipe insulation. |
| Cooler removal | `pipeleg_upper_04_reducer`, `pipeleg_upper_05_cooler`, `pipeleg_upper_06_reducer` | Fixed cooling removal patches, scaled in corrected-Q perturbations. |
| Passive ambient walls | Remaining wall patches with `rcExternalTemperature` / `externalTemperature` | Carry patch-level BC type and emissivity status. |

AGENT-204 adds the supporting detail that the main piplegs have the `1.4 in`
layer, while the test section is quartz/no main-pipe insulation. That
distinction matters: a single global 1D insulation thickness is not a literal
CFD match for the test section.

## 1D Geometry / BC Contract

The current TAMU Fluid 1D model is a reduced-order loop model, not a direct
OpenFOAM boundary-condition clone.

Geometry from `geometry.py`:

| Segment | Length/shape contract | Diameter/wall contract | Special role |
| --- | --- | --- | --- |
| `left_lower_vertical` | TP3 to TP4, 14.34 in vertical | 0.87 in ID, 1.0 in OD, SS316L, insulated | Upcomer lower leg. |
| `test_section` | TP4 to TP5, 7.32 in vertical | 0.835 in ID, 0.943 in OD, quartz, `insulated=False` | Quartz test-section source. |
| `left_upper_vertical` | TP5 to TP6, 14.34 in vertical | 0.87 in ID, 1.0 in OD, SS316L, insulated | Upcomer upper leg. |
| `cooled_incline_*` | 36 in top incline split into pre-HX, 12 in active HX, post-HX | 0.87 in ID, 1.0 in OD, SS316L, insulated | Air-side cooler region. |
| `right_vertical` | 36 in downcomer | 0.87 in ID, 1.0 in OD, SS316L, insulated | Downcomer. |
| `heated_incline` | 36 in lower incline | 0.87 in ID, 1.0 in OD, SS316L, insulated | Uniform full-length heater source in baseline mode. |
| horizontal stubs | 1 in connector stubs | 0.87 in ID, 1.0 in OD, SS316L, insulated | Geometric closure / loss accounting. |

Default 1D refinement is sensor-aware with a `0.15 m` maximum subsegment length.
The older coarse parent-segment mesh is a diagnostic/regression reference only
for thermal-closure arguments.

1D operating inputs from `configs/cases.yaml`:

| Case | Main heater W | Test-section W | Air inlet C | Air flow Lpm |
| --- | ---: | ---: | ---: | ---: |
| Salt 1 | 232.3 | 37.0 | 25.96 | 37.0 |
| Salt 2 | 265.7 | 37.0 | 26.04 | 37.0 |
| Salt 3 | 297.5 | 37.0 | 26.64 | 37.0 |
| Salt 4 | 337.6 | 37.0 | 26.82 | 37.0 |

1D scenario fields from `solver.py` / `scenarios.yaml`:

- `insulation_thickness_in` is a scenario scalar in the baseline wall-to-ambient
  resistance model. It is commonly swept over `0, 1, 2, 3 in`; practical reduced
  studies also use `1.0 in` and `2.0 in` families.
- `radiation_on` is a 1D model switch. It is not equivalent to the CFD label
  above unless the comparison explicitly states the mapping.
- `model_mode=predictive_airside_hx` solves the cooling-jacket duty from the
  air-side boundary, loop field, and hydraulic closure.
- measured TP/TW, measured mass flow, measured velocity, measured cooler duty,
  and measured air outlet are validation-only inputs in the reporting layer.
- salt cases include main heater power plus `37 W` through the quartz test
  section; water active-contract cases use heater power only with
  `test_section_power_W = 0.0`.

Interpretation rule: a 1D row must be labeled by its explicit scenario fields
(`insulation_thickness_in`, `radiation_on`, model mode, closure overrides, and
any 3D contract flags). It should not be described as "the CFD 1.4 in setup"
unless a per-segment insulation/emissivity contract has been implemented and
declared.

## Current Corrected-Q Run State

Current scheduler snapshot on 2026-07-08:

| Job | Name | State | Role |
| --- | --- | --- | --- |
| `3275448` | `corr_saltq_g1` | RUNNING | Salt1 lo10/hi10 and Salt2 lo10/lo5. |
| `3275449` | `corr_saltq_g2` | RUNNING | Salt2 hi5/hi10 and Salt3 lo10/lo5. |
| `3275560` | `corr_saltq_salt4_all` | RUNNING | Salt4 lo10/lo5/hi5/hi10 replacement. |
| `3280969` | `saltq_gate_after` | PENDING | Formal gate with dependency `afterany:3275448:3275449:3275560`. |

The continuation/gate job ID issue is therefore not a mismatch: `3280969` is
the corrected gate and its dependency is the current accepted terminal set. The
important caveat is policy, not ID syntax: the gate must treat failed, canceled,
or timeout cases as non-requalified rather than admitting them.

Latest live monitor values from `tmp/2026-07-08_AGENT-205_live_monitor`:

| Case | Latest solver time s | Status |
| --- | ---: | --- |
| `salt1_jin_lo10q_corrected` | 5946.805 | Running; special scrutiny because Salt 1 lacks nominal mdot reference. |
| `salt1_jin_hi10q_corrected` | 4010.590 | Ended early via convergence monitor after 254.259 s past restart; special scrutiny. |
| `salt2_jin_lo10q_corrected` | 9894.049 | Running; hold for formal gate. |
| `salt2_jin_lo5q_corrected` | 9888.363 | Running; hold for formal gate. |
| `salt2_jin_hi5q_corrected` | 9474.017 | Running; hold for formal gate. |
| `salt2_jin_hi10q_corrected` | 9381.894 | Running; hold for formal gate. |
| `salt3_jin_lo10q_corrected` | 9130.330 | Running; hold for formal gate. |
| `salt3_jin_lo5q_corrected` | 9095.669 | Running; hold for formal gate. |
| `salt3_jin_hi5q_corrected` | 7639.476 | Bad/investigate; old job `3275450` has fatal/error markers. |
| `salt3_jin_hi10q_corrected` | 7637.876 | Bad/investigate; old job `3275450` has fatal/error markers. |
| `salt4_jin_lo10q_corrected` | 11363.047 | Running in replacement Salt4-all job; hold for gate. |
| `salt4_jin_lo5q_corrected` | 11400.657 | Running in replacement Salt4-all job; hold for gate. |
| `salt4_jin_hi5q_corrected` | 11149.486 | Running in replacement Salt4-all job; hold for gate. |
| `salt4_jin_hi10q_corrected` | 11265.085 | Running in replacement Salt4-all job; hold for gate. |

This answers the "latest relevant window" question: yes, current interpretation
must use the current live corrected-Q windows above, not the older June 19/25
perturbation windows and not only the AGENT-202 snapshot.

## Salt 1 Normal / Base Continuation Status

Salt 1 has two separate facts that should not be conflated:

1. The June 25 normal relaunch chain for `salt1_jin_basecont` was submitted as
   jobs `3259065` through `3259069`, but `sacct` reports all five were
   `CANCELLED by 890970` before running (`Elapsed=00:00:00`, end
   `2026-06-26T11:48:47`).
2. The staged `salt1_jin_basecont` case tree nevertheless contains retained
   processor times through `4026.15625 s`, and its
   `logs/log.foamRun_continuation` ends cleanly after
   `convergenceMonitor: CONVERGED`.

Therefore, the Salt 1 base-continuation tree is usable as a later Salt 1
qualification candidate than the June 18 `3756.33125 s` tree, but it should not
be described as a successful June 25 Slurm chain completion. Salt 1 remains
held for qualification before closure fitting.

## Run-Submission Guidance

There is no immediate additional run that should be submitted before the
formal corrected-Q gate `3280969` runs, unless we decide to spend compute on a
known gap despite the active jobs still running.

Do not repeat these now:

- Salt 1 lower heat input: `salt1_jin_lo10q_corrected` is already running in
  `3275448`.
- Salt 4 higher heat input: `salt4_jin_hi5q_corrected` and
  `salt4_jin_hi10q_corrected` are already running in `3275560`.
- Old June 19/25 perturbation runs: treat them as superseded by the corrected
  July 4 wave unless a note explicitly re-admits a row for historical
  comparison.

If a 1/4-node Salt 1 continuation is later justified, the best non-duplicative
node-fill candidates are, in order:

1. `salt3_jin_hi5q_corrected` and `salt3_jin_hi10q_corrected` reruns, because
   the old `3275450` products advanced only about 20 s past restart and carry
   fatal/error markers.
2. A Salt 1 nominal/base continuation from the best retained Salt 1 source, if
   the formal gate or qualification package says the `4026.15625 s`
   base-continuation candidate is still too weak for the intended comparison.
3. A Salt 1 high-Q continuation/rerun with the convergence monitor made
   diagnostic-only, because the current high-Q stopped at `4010.590361446 s`
   after only `254.259 s` past restart.
4. Salt 1 low-Q or Salt 4 high-Q only if the running jobs fail, time out, or the
   formal gate marks them non-requalified.

The conservative plan is to let `3275448`, `3275449`, and `3275560` finish, run
gate `3280969`, then submit only the failed or non-admitted gaps.

## Documentation Rules Going Forward

Every closure observation or comparison table should carry:

- CFD case root and retained time window.
- CFD setup label:
  `1.4in_layer_present__surface_emissivity_bc_present_no_volume_radiation_field`.
- Whether the row is mainline, corrected-Q perturbation, historical
  perturbation, or Salt 1 qualification-only.
- 1D scenario name plus explicit `insulation_thickness_in`, `radiation_on`,
  `model_mode`, and closure overrides.
- A flag for whether the 1D setup is a literal BC match, a diagnostic
  temperature-matching setup, or a fitted/closure-informed scenario.

Rows missing those fields should be blocked from closure fitting and from
publication-grade comparison tables until repaired.
