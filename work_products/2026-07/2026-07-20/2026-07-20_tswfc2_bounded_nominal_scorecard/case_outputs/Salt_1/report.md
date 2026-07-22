# Salt 1 — tswfc2_smoke_salt2_four_node_v1

## Summary

- Working fluid: `salt`
- Property set: `salt_jin`
- Mode: `predictive_airside_hx`
- Radiation: `False`
- Effective insulation thickness: `1.0` in
- Ambient temperature: `300.00` K
- Effective air flow: `37.00` L/min
- Effective air inlet temperature: `299.11` K
- Predicted air outlet temperature: `371.88` K
- Measured air outlet temperature: `385.95` K
- Predicted mass flow rate: `0.019690` kg/s
- Measured mass flow rate: `0.015800` kg/s
- Mass-flow error: `+0.003890` kg/s
- Predicted main-tube velocity: `0.027060` m/s
- Measured area-weighted mean velocity: `0.018500` m/s
- Velocity error: `+0.008560` m/s
- Predicted main-tube Reynolds number: `280.30`
- Buoyancy pressure: `30.8541` Pa
- Loss pressure: `30.8541` Pa
- Pressure residual |loss-buoyancy|: `0.000000` Pa
- Predicted HX duty: `49.6280` W
- Measured cooler duty: `55.5800` W
- Predicted ambient heat loss: `219.6723` W
- Temperature periodicity error: `1.247713e-09` K
- Temperature scan bounds: `274.11` to `550.00` K
- Temperature scan expansions: `0`
- Temperature scan best endpoint side: `interior`
- Root status: `accepted`
- Accepted for validation metrics: `True`
- Validity status: `valid`
- Max bulk temperature: `528.84` K
- Minimum viscosity used in closure: `4.041797e-03` Pa·s
- Solver lineage: `scientific_reset_pre_revalidation_v1`
- Scientific trust policy: `2026-05-29_scientific_reset_v1`
- Paper admissibility: `not_paper_eligible_pending_revalidation`

## Validation Policy

- Validation data enter only in reporting. The active solver does not use measured TP/TW, measured mass flow, or measured HX duty as runtime inputs.
- `TW10` is reported separately as a cooling-jacket shell surrogate.
- The unlabeled `TW11 (K)` source values remain excluded from active use and are preserved only for provenance in `validation_data/validation_cases.csv`.