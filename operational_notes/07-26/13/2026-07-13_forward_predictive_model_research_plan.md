# Forward Predictive Model Research Plan

Task: `AGENT-286`
Date: 2026-07-13
Tags: #predictive-1d #thermal-parity #forward-model #heat-loss #mdot #sensor-prediction

## Start Here

The durable package is:

`work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/`

Read in this order:

1. `README.md`
2. `input_readiness_matrix.csv`
3. `blocker_register.csv`
4. `research_plan.md`
5. `task_backlog.csv`

## One-Sentence Status

We can run a forward 1D model, but we cannot yet make a thesis-strength claim
that it predicts mdot and sensor temperatures from heater/cooling setup alone,
because cooler/HX, heater transfer, test-section source/loss, wall-layer
mapping, radiation separability, and thermal uncertainty gates are unresolved.

## Recommended Next Step

Claim `TODO-PRED-INPUT-CONTRACT`, then `TODO-PRED-FORWARD-V0`.

The forward-v0 should solve mdot and sensor temperatures using heater input and
imposed cooler duty. It must not use CFD mdot or realized CFD wall flux at
runtime. That mode is not the final HX-predictive model, but it is the cleanest
way to debug pressure-rooted mdot and the thermal source/wall contracts before
fitting an HX UA or epsilon-NTU model.

## Related Work

- AGENT-270 predictive heat-loss path
- AGENT-279 no-radiation heater/cooler parity
- AGENT-281 wall-layer mapping recommendations
- AGENT-284 Salt2 Closure-QOI mesh/GCI gate
- AGENT-285 lit-rev synthesis next steps
