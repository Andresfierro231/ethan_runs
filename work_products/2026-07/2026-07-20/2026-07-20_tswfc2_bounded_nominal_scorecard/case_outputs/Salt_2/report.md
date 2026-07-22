# Salt 2 — tswfc2_smoke_salt2_four_node_v1

## Summary

- Working fluid: `salt`
- Property set: `salt_jin`
- Mode: `predictive_airside_hx`
- Radiation: `False`
- Effective insulation thickness: `1.0` in
- Ambient temperature: `300.00` K
- Effective air flow: `37.00` L/min
- Effective air inlet temperature: `299.19` K
- Predicted air outlet temperature: `379.30` K
- Measured air outlet temperature: `387.44` K
- Predicted mass flow rate: `0.022191` kg/s
- Measured mass flow rate: `0.016800` kg/s
- Mass-flow error: `+0.005391` kg/s
- Predicted main-tube velocity: `0.030742` m/s
- Measured area-weighted mean velocity: `0.019600` m/s
- Velocity error: `+0.011142` m/s
- Predicted main-tube Reynolds number: `365.31`
- Buoyancy pressure: `31.1657` Pa
- Loss pressure: `31.1657` Pa
- Pressure residual |loss-buoyancy|: `0.000000` Pa
- Predicted HX duty: `54.2987` W
- Measured cooler duty: `56.3400` W
- Predicted ambient heat loss: `248.4017` W
- Temperature periodicity error: `8.847110e-10` K
- Temperature scan bounds: `274.19` to `550.00` K
- Temperature scan expansions: `0`
- Temperature scan best endpoint side: `interior`
- Root status: `accepted`
- Accepted for validation metrics: `True`
- Validity status: `valid`
- Max bulk temperature: `549.03` K
- Minimum viscosity used in closure: `3.495678e-03` Pa·s
- Solver lineage: `scientific_reset_pre_revalidation_v1`
- Scientific trust policy: `2026-05-29_scientific_reset_v1`
- Paper admissibility: `not_paper_eligible_pending_revalidation`

## Validation Policy

- Validation data enter only in reporting. The active solver does not use measured TP/TW, measured mass flow, or measured HX duty as runtime inputs.
- `TW10` is reported separately as a cooling-jacket shell surrogate.
- The unlabeled `TW11 (K)` source values remain excluded from active use and are preserved only for provenance in `validation_data/validation_cases.csv`.