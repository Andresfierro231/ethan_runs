---
provenance:
  - .agent/BOARD.md
  - .agent/BLOCKERS.md
  - operational_notes/07-26/16/2026-07-16_FLUID_WALLS_TOMORROW_HANDOFF.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/setup_only_hx_boundary_scorecard.csv
  - work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/hx_candidate_gate_decision.csv
  - work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m3ts_coupled_scorecard.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
tags: [forward-model, cooler, hx, setup-only, test-plan, predictive-1d]
related:
  - TODO-PREDICT-COOLER-REMOVAL
  - predictive-wall-test-section-submodels
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-480
date: 2026-07-17
role: Coordinator/Writer/Tester
type: operational_note
status: complete
---
# Cooler Model Comprehensive Test Plan

## Why This Exists

The current setup-legal cooler/HX lane is promising but not yet a comprehensive
model-form comparison. AGENT-438/454 admitted `salt2_fit_constant_UA_bulk_drive`
as a boundary submodel screen: Salt2 train error `0 W`, Salt3 validation error
`2.869104004 W`, Salt4 holdout error `7.502618613 W`, runtime violations `0`.
AGENT-461 then completed the coupled M3+TS Fluid scorecard, but the live blocker
remains open because no candidate has both an admitted coupled gate and held-out
heat-loss/test-section gates.

The next implementer should test two cooler models under the same split and
runtime-leakage contract:

1. Constant-UA effectiveness/NTU cooler.
2. Segmented distributed-UA cooler.

The key scientific distinction is total duty versus spatial placement. A model
can match total `Q_hx` but still place the cooling at the wrong loop location,
which can hurt mdot, TP, and TW scores. This plan therefore requires both a
duty-only scorecard and a coupled Fluid scorecard.

## Open First

Open these before editing:

1. `.agent/BOARD.md`
2. `.agent/BLOCKERS.md`
3. `operational_notes/07-26/16/2026-07-16_FLUID_WALLS_TOMORROW_HANDOFF.md`
4. `operational_notes/maps/forward-predictive-model.md`
5. `operational_notes/maps/thermal-boundary-and-radiation.md`
6. `work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/README.md`
7. `work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/README.md`
8. `work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/README.md`
9. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`

Claim `TODO-PREDICT-COOLER-REMOVAL` or a narrow follow-on agent row before
implementation. If Fluid source changes are needed, also claim a non-overlapping
row in `../cfd-modeling-tools/.agent/BOARD.md`.

## Trusted Starting Facts

- Current Fluid already computes predictive air-side HX duty with an
  effectiveness/NTU calculation and `ScenarioConfig.hx_ua_multiplier`.
- The active Fluid implementation computes `UA = hx_ua_multiplier * L /
  (R_i' + R_wall' + R_air')`, then `NTU = UA / C_min` and `Q = epsilon C_min
  max(T_fluid,in - T_air,in, 0)`.
- `salt2_fit_constant_UA_bulk_drive` is the preferred current setup-legal
  candidate: Salt3 `2.869 W`, Salt4 `7.503 W`, all-non-Salt1 RMSE
  `4.63756559107 W`.
- A prior global post-solve HX multiplier passed Salt3 but failed Salt4
  (`17.51086742 W` holdout error), so any new model must show holdout
  generalization rather than just fitting Salt2.
- Runtime-forbidden inputs remain: realized CFD `wallHeatFlux`, CFD mdot,
  imposed CFD cooler duty, validation/holdout temperatures, and validation/
  holdout cooler targets as runtime inputs. Cooler targets are scoring-only
  except Salt2 fit.

## Model 1: Constant-UA Effectiveness/NTU

Purpose: establish the simplest physically interpretable cooler model and
preserve the AGENT-438 candidate as the baseline.

Definition:

```text
UA_case = alpha_UA * UA_setup(case)
C_hot = mdot_fluid * cp_fluid
C_cold = mdot_air * cp_air
C_min = min(C_hot, C_cold)
C_r = C_min / C_max
NTU = UA_case / C_min
epsilon = epsilon_counterflow_or_declared_flow_arrangement(NTU, C_r)
Q_hx = epsilon * C_min * max(T_fluid,in - T_air,in, 0)
```

Fit policy:

- Fit exactly one scalar, `alpha_UA`, on Salt2 only.
- Freeze `alpha_UA` before Salt3 and Salt4.
- Do not use Salt3/Salt4 cooler duty, mdot, or temperatures to tune the model.
- Treat model-form choices such as flow arrangement as predeclared candidates,
  not as tuned per-case switches.

Minimum score rows:

- Salt2 train, Salt3 validation, Salt4 holdout.
- Duty-only score: predicted `Q_hx`, scoring-only target `Q_hx`, error W, error
  percent, runtime-input audit.
- Coupled score: solve with the same frozen `alpha_UA` inside Fluid, then report
  mdot error percent, TP RMSE, TW RMSE, all-probe RMSE, Tmean error, loop-dT
  error, root status, and total `Q_hx`.

Expected result:

- It should reproduce or closely match the existing `salt2_fit_constant_UA_bulk_drive`
  duty scores. If it does not, stop and explain the discrepancy before adding
  model complexity.

## Model 2: Segmented Distributed-UA Cooler

Purpose: test whether matching heat removal location along the cooler improves
loop temperature placement after total duty is already reasonable.

Definition:

- Split the active cooler/HX length into `N` axial cells, with `N` predeclared
  values such as `4`, `8`, and `16` for convergence testing.
- Assign each cell a setup-derived local UA:

```text
UA_i = alpha_UA * UA_setup_total * length_fraction_i
```

- March the fluid temperature cell-by-cell:

```text
Q_i = epsilon_i * C_min_i * max(T_fluid,i - T_air,i, 0)
T_fluid,i+1 = T_fluid,i - Q_i / (mdot_fluid cp_fluid)
T_air,next = T_air,i + Q_i / (mdot_air cp_air)
Q_hx_total = sum_i Q_i
```

- Use the physical air-flow direction if it is documented. If not documented,
  score co-current and counterflow direction as named sensitivity rows, not as
  extra fitted parameters.

Fit policy:

- Fit exactly one global scalar, `alpha_UA`, on Salt2 only.
- Freeze `alpha_UA`, `N`, and air-flow-direction assumption before Salt3/Salt4
  scoring.
- Do not allow per-cell fitted UA, per-case correction factors, or validation
  temperature feedback.

Minimum diagnostics:

- `Q_i`, `T_fluid_i`, `T_air_i`, local `NTU_i`, local `epsilon_i`, and cumulative
  heat removal by axial cell.
- Grid convergence of the segmented result: `N=4`, `8`, `16`. The candidate is
  not credible if score changes materially with `N`.
- Comparison to lumped constant-UA duty and coupled TP/TW residual patterns.

Expected result:

- If total `Q_hx` is similar to Model 1 but TP/TW scores improve, the issue was
  spatial heat placement.
- If total `Q_hx` improves but TP/TW do not, the remaining mismatch is likely
  upstream heater/test-section/passive-wall/junction placement or hydraulic
  coupling, not cooler duty magnitude.
- If the segmented model only improves by introducing extra effective degrees of
  freedom, reject it.

## Required Outputs

Recommended implementation package:

```text
tools/analyze/build_cooler_removal_model.py
tools/analyze/test_cooler_removal_model.py
work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model/
```

The package should contain:

- `candidate_definitions.csv`: model id, equations, fitted parameter count,
  flow-arrangement assumption, segmentation count.
- `fit_parameters.csv`: Salt2-only fit values and fit residuals.
- `duty_scorecard.csv`: Salt2/Salt3/Salt4 cooler-duty scores.
- `coupled_scorecard.csv`: Fluid mdot/TP/TW/all-probe/Tmean/loop-dT scores.
- `segmented_profile_diagnostics.csv`: only for segmented rows; local `Q_i`,
  temperatures, NTU, epsilon, and cumulative heat.
- `runtime_input_audit.csv`: explicit pass/fail for forbidden inputs.
- `model_comparison_decision.json`: selected candidate, why, and blocker
  decision.
- `source_manifest.csv`: exact sources and use of each.
- `README.md`: observed facts, interpretation, failed candidates, blockers,
  next action.

## Gates

Use two gate tiers.

Duty screen:

- Validation Salt3: `abs_error_W <= 5 W`.
- Holdout Salt4: `abs_error_W <= 10 W`.
- Runtime input violations: `0`.
- Fitted degrees of freedom: `1`.

Coupled screen:

- All Fluid roots must be accepted or explicitly diagnosed.
- Predeclare mdot/TP/TW thresholds before final admission. Until then, report
  these as scorecard metrics rather than claiming final admission.
- Provisional comparison targets are the AGENT-461 completed M3+TS scorecard:
  Salt3 mdot error `14.05689347%`, TP RMSE `6.17325796 K`, TW RMSE
  `19.25285014 K`; Salt4 mdot error `13.81175726%`, TP RMSE `5.955946227 K`,
  TW RMSE `20.90047181 K`.
- A cooler model should not be promoted if it improves duty while materially
  worsening coupled mdot or TP/TW placement.

Final blocker impact:

- Passing the cooler test alone does not close
  `predictive-wall-test-section-submodels`.
- It can remove cooler uncertainty from that blocker only if it passes duty,
  runtime, and coupled score screens without runtime leakage.
- The blocker still also needs admitted wall/test-section/passive-boundary
  heat-loss behavior.

## Test Plan

Unit tests:

- `UA=0` gives `Q_hx=0`.
- Larger `alpha_UA` gives nondecreasing `Q_hx`.
- `T_fluid_in <= T_air_in` gives no cooling unless a declared model allows heat
  reversal.
- Energy conservation: `sum(Q_i)` equals fluid enthalpy decrease and air
  enthalpy increase within tolerance.
- Segmented `N` convergence is monotonic or explicitly bounded.
- Fit code uses only Salt2 rows.
- Runtime audit fails if Salt3/Salt4 target duty, validation temperatures, CFD
  mdot, or realized `wallHeatFlux` enter runtime input columns.

Regression tests:

- Reproduce AGENT-438 constant-UA scores within a declared tolerance before
  adding segmented candidates.
- Verify `candidate_definitions.csv`, `fit_parameters.csv`,
  `duty_scorecard.csv`, `coupled_scorecard.csv`, `runtime_input_audit.csv`,
  `source_manifest.csv`, `summary.json`, and `README.md` are emitted with
  required columns.

Compute tests:

- Run the duty-only scorecard locally.
- Run coupled Fluid scoring on a compute node. If an unbounded coupled run is
  expected to exceed one hour, submit a bounded sbatch job rather than running
  on the login node.
- Preserve partial rows if a coupled solve fails; do not overwrite completed
  scorecards with an all-timeout artifact.

Review tests:

- Compare each candidate against current AGENT-438/454/461 rows.
- Check that no candidate is selected only because it has more hidden fitted
  parameters.
- Confirm TW10 stays excluded unless the model emits an active-HX shell-state
  temperature with finite provenance.

## Blockers And Fallbacks

- If Fluid source modification is required for segmented UA, claim the external
  Fluid board first and add focused Fluid tests.
- If air-flow direction or active HX geometry is ambiguous, publish that as a
  geometry/setup blocker and run co-current/counterflow only as sensitivity
  rows.
- If Model 1 already passes duty but neither model improves coupled TP/TW, stop
  cooler escalation and return to wall/test-section/passive-boundary placement.
- If Model 2 improves Salt3 but fails Salt4, keep it as diagnostic model-form
  evidence and do not promote it.

## Do-Not-Do Guardrails

- Do not mutate native CFD outputs.
- Do not use imposed CFD cooler duty as a runtime boundary condition.
- Do not fit Salt3 or Salt4.
- Do not let internal Nu absorb cooler, heater, passive-wall, radiation, storage,
  or test-section residuals.
- Do not add per-segment fitted UA values; the segmented model gets one global
  scalar only.
- Do not claim final forward-v1 admission from the cooler scorecard alone.
