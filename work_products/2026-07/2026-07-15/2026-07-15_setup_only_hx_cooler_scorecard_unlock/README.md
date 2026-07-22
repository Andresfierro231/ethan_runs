# Setup-Only HX/Cooler Scorecard Unlock

Date: 2026-07-15
Task: AGENT-438

## Result

The preferred setup-only HX/cooler lane,
`salt2_fit_constant_UA_bulk_drive`, passes this bounded candidate score gate:

- Salt2 train error: `0 W`.
- Salt3 validation error: `2.869104004 W`
  against a `5.0 W` gate.
- Salt4 holdout error: `7.502618613 W`
  against a `10.0 W` gate.
- Runtime input violations: `0`.

This advances the HX/cooler lane as a setup-only final-scorecard input. It does
not admit final forward-v1. Hydraulic pressure/F6, internal-Nu/thermal
sign/heat-balance, recirculation, and mesh/GCI gates still block final
promotion.

## Outputs

- `setup_only_hx_boundary_scorecard.csv`
- `hx_candidate_gate_decision.csv`
- `hx_runtime_input_legality_audit.csv`
- `forward_v1_remaining_unlock_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Math and Gate Assumptions

For each case:

`error_W = abs(predicted_qhx_W - target_qhx_W_for_scoring_only)`

`relative_error_pct = 100 * error_W / abs(target_qhx_W_for_scoring_only)`

The target cooler duty is used only for post-prediction scoring. It is not a
runtime input. The split discipline is Salt2 fit, Salt3 validation, Salt4
holdout. The fitted scalar is frozen after Salt2.

AGENT-438 uses a deliberately narrow score gate:

- validation `error_W <= 5.0`
- holdout `error_W <= 10.0`
- runtime input violation count equals zero

These tolerances are a candidate-screen gate, not a publication uncertainty
claim.

## Remaining Blockers

The shortest remaining chain is:

1. Use this package as the HX/cooler input to the final forward-v1 scorecard.
2. Admit hydraulic pressure/F6 rows or keep them diagnostic with a separate
   section-effective model lane.
3. Resolve internal-Nu sign/heat-balance if any true Nu fit is required.
4. Carry mesh/GCI uncertainty into pressure and thermal QoIs.
5. Rebuild the final scorecard without realized CFD wallHeatFlux, imposed CFD
   cooler duty, CFD mdot, validation pressure, or validation temperature runtime
   leakage.

## Guardrails

- No native CFD solver outputs were mutated.
- No scheduler jobs were launched.
- Registry/admission state and generated indexes were not mutated.
- External `../cfd-modeling-tools` was kept read-only.
- Current PM5/upcomer rows remain diagnostic-only for true single-stream
  coefficients.
