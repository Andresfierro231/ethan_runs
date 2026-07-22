---
task: AGENT-296
date: 2026-07-13
role: Coordinator/Writer
type: handoff
status: complete
tags: [forward-model, predictive-1d, parallel-plan, thesis-source]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/README.md
  - operational_notes/07-26/13/2026-07-13_NEXT_PHASE_ANALYSIS_AND_LITERATURE_HANDOFF.md
---
# Predictive Parallel Progress And Next Plan

Generated: `2026-07-13`

This handoff consolidates the parallel-agent progress toward an end-to-end
predictive 1D heat-loss model. The target remains: physical setup inputs in
(heater/cooler rates and geometry/boundaries), predicted mass flow and sensor
temperatures out, without using CFD mdot, realized CFD wall heat flux, or
validation temperatures at runtime.

## What Is Established

- The strict predictive input contract exists and passes: runtime fields,
  calibrated parameters, validation targets, and diagnostic-only CFD evidence
  are separated.
- The current split is locked: `salt_2` train, `salt_3` validation, `salt_4`
  holdout, `salt1_nominal` diagnostic-only, corrected-Q and low-heat blocked
  pending row-specific admission.
- Forward-v0 with imposed cooler and heater-only source is executable. It
  substantially improves CFD Tmean error but still overpredicts mdot.
- The hydraulic gate found a real pressure-rooted blocker: forward-v0 mdot is
  high for every Salt row, so friction/minor-loss/profile correction must
  precede thermal parameter fitting.
- The heater/test-section contract supports heater-only as the next unfitted
  source model. Positive fluid test-section heat is not fit-safe from current
  evidence.
- The HX fit lane has now produced a split-aware provisional global HX duty
  multiplier score. It improves validation Tmean error for the heater-only
  variant, but it is still entangled with the mdot blocker and fast-scan
  acceptance limits.
- Wall-shell sampling exists, and E1/E2 wall-layer mappings run, but they do
  not close the passive heat-loss gap. They remain diagnostic until the external
  boundary API and thermal uncertainty gates mature.
- CFD `rcExternalTemperature` realized wallHeatFlux embeds emissivity/Tsur
  effects. Treat "no radiation" replays only as sensitivities unless a future
  package provides a separable radiation term or controlled rerun.

## What Is Not Yet Thesis-Strength

- No calibrated thermal correction is yet admissible as a final predictive
  claim because hydraulic mdot error is still large.
- Effective internal HTC/Nu/UA tables remain blocked for closure fitting until
  thermal mesh/sign/heat-balance gates pass.
- Sensor-temperature claims remain secondary until TP/TW mapping is explicitly
  bounded.
- Corrected-Q and low-heat cases are not admitted into the predictive split.
- Full Fluid `solve_case` confirmation for forward-v0 is prepared but not yet
  submitted or completed.

## Scientific Ordering

1. Confirm forward-v0 fast-scan findings with full `solve_case`.
2. Correct hydraulics using fit-safe pressure rows before fitting thermal
   terms.
3. Freeze a low-dimensional HX/cooler correction trained only on `salt_2`.
4. Combine heater-only, admitted hydraulic correction, and HX correction into a
   forward-v1 score.
5. Add wall/external-boundary dictionaries and wall-layer comparisons as a
   separate physical boundary lane, not as per-case heat hacks.
6. Admit thermal HTC/Nu/UA only after Salt2 thermal mesh/sign gates are clear.
7. Score train/validation/holdout and then add corrected-Q/low-heat only after
   their own admission gates.

## Parallel Plan

The immediate maximum-progress plan is in `parallel_agent_plan.csv`. The short
version:

- Agent A: submit/monitor the prepared full `solve_case` confirmation if compute
  use is allowed.
- Agent B: build hydraulic correction candidates from fit-safe pressure spans
  and re-score mdot without thermal fitting.
- Agent C: reconcile the HX package status and freeze the one-scalar HX
  correction policy using the current validation split.
- Agent D: design/implement first-class external boundary dictionaries for
  Fluid/bridge tooling without realized wallFlux replay.
- Agent E: run Salt2 thermal mesh/sign admission once AGENT-291 fine thermal
  evidence is harvested.
- Agent F: build the TP/TW sensor map contract so final scores can include
  sensor temperatures with stated uncertainty.
- Agent G: assemble forward-v1 only after A/B/C have usable outputs.

## Acceptance For The Next Phase

The next phase should not be judged by a single improved temperature number.
It should be accepted only if it publishes:

- runtime input audit with no diagnostic CFD leakage;
- train/validation/holdout split table;
- mdot and pressure residual improvement from a hydraulic-only correction;
- HX/cooler correction trained on `salt_2` and scored on `salt_3`/`salt_4`;
- residual attribution by hydraulic, heater/test-section, cooler/HX, passive
  wall/external boundary, and sensor lanes;
- blocker table for unresolved mesh, corrected-Q, low-heat, and sensor limits.

## Files

- `parallel_agent_plan.csv`: proposed parallel lanes and acceptance signals.
- `decision_gate_table.csv`: gates that must pass before claims escalate.
- `summary.json`: compact machine-readable state.

