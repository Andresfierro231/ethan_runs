---
task: AGENT-296
date: 2026-07-13
role: Coordinator/Writer
type: operational-note
status: complete
tags: [forward-model, predictive-1d, parallel-plan, thesis-source]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_parallel_progress_and_next_plan/README.md
  - operational_notes/maps/forward-predictive-model.md
  - .agent/BOARD.md
---
# 2026-07-13 Predictive Parallel Progress And Next Plan

## Start Here

Primary package:
`work_products/2026-07/2026-07-13/2026-07-13_predictive_parallel_progress_and_next_plan/`

This note exists so the next agents can continue the predictive heat-loss path
without relying on chat context. The active goal is still predictive: given
physical heater/cooler setup and model parameters, predict mdot and sensor
temperatures. Diagnostic CFD fields may be used for fitting/scoring only under
the declared split; they must not become runtime inputs.

## Current Practical State

The project now has enough infrastructure to move from "what inputs are
available?" to "which low-dimensional physical corrections actually improve
held-out predictions?" The limiting blocker is not a missing script. It is
scientific ordering:

1. mdot is still overpredicted, so hydraulics must be corrected before thermal
   fitting.
2. HX/cooler is first-order, but only one scalar can be trained under the
   current Salt2/Salt3/Salt4 split.
3. Wall-layer and external BC work must avoid realized CFD wallFlux replay and
   double radiation.
4. Internal HTC/Nu/UA cannot enter thesis-strength closure fitting until thermal
   mesh, sign, heat-balance, and downcomer gates pass.

## Parallel Work Recommendation

Launch separate agents only where their edit paths do not overlap:

- Agent A: submit/monitor the prepared full `solve_case` confirmation from
  AGENT-293 if compute submission is allowed.
- Agent B: hydraulic correction from fit-safe pressure rows only.
- Agent C: HX fit status reconciliation and one-scalar split freeze.
- Agent D: Fluid/bridge external boundary dictionary design or prototype.
- Agent E: Salt2 thermal mesh/sign gate after AGENT-291 evidence is harvested.
- Agent F: sensor map contract.
- Agent G: forward-v1 scorecard only after A/B/C produce usable outputs.

The detailed lane contract is in `parallel_agent_plan.csv`.

## Guardrails

- Do not mutate native CFD outputs.
- Do not use CFD mdot, realized wallHeatFlux, or validation temperatures as
  runtime inputs.
- Do not fit thermal terms until hydraulic mdot error is addressed.
- Do not use per-case HX/heater/wall multipliers.
- Do not claim CFD radiation-off parity; current CFD wallHeatFlux embeds
  `rcExternalTemperature` emissivity/Tsur effects.
- Do not admit corrected-Q or low-heat rows without row-specific latest-time
  and input-contract admission.

## Next Acceptance Target

The next major deliverable should be a forward-v1 split scorecard with:

- heater-only source contract;
- admitted hydraulic correction;
- one-scalar HX/cooler correction;
- train/validation/holdout scores;
- residual attribution by hydraulic, HX/cooler, heater/test-section, passive
  external wall, and sensors;
- explicit blockers for thermal mesh, sensor, corrected-Q, and low-heat claims.

