# Salt 3 — tswfc2_smoke_salt2_four_node_v1

## Summary

- Working fluid: `salt`
- Property set: `salt_jin`
- Mode: `predictive_airside_hx`
- Radiation: `False`
- Effective insulation thickness: `1.0` in
- Ambient temperature: `300.00` K
- Effective air flow: `37.00` L/min
- Effective air inlet temperature: `299.79` K
- Predicted air outlet temperature: `386.63` K
- Measured air outlet temperature: `395.75` K
- Predicted mass flow rate: `0.024401` kg/s
- Measured mass flow rate: `0.017500` kg/s
- Mass-flow error: `+0.006901` kg/s
- Predicted main-tube velocity: `0.034052` m/s
- Measured area-weighted mean velocity: `0.020500` m/s
- Velocity error: `+0.013552` m/s
- Predicted main-tube Reynolds number: `451.50`
- Buoyancy pressure: `31.5815` Pa
- Loss pressure: `31.5815` Pa
- Pressure residual |loss-buoyancy|: `0.000000` Pa
- Predicted HX duty: `58.4370` W
- Measured cooler duty: `60.5500` W
- Predicted ambient heat loss: `276.0634` W
- Temperature periodicity error: `-1.853323e-09` K
- Temperature scan bounds: `274.79` to `687.61` K
- Temperature scan expansions: `1`
- Temperature scan best endpoint side: `interior`
- Root status: `accepted`
- Accepted for validation metrics: `True`
- Validity status: `valid`
- Max bulk temperature: `567.34` K
- Minimum viscosity used in closure: `3.110415e-03` Pa·s
- Solver lineage: `scientific_reset_pre_revalidation_v1`
- Scientific trust policy: `2026-05-29_scientific_reset_v1`
- Paper admissibility: `not_paper_eligible_pending_revalidation`

## Validation Policy

- Validation data enter only in reporting. The active solver does not use measured TP/TW, measured mass flow, or measured HX duty as runtime inputs.
- `TW10` is reported separately as a cooling-jacket shell surrogate.
- The unlabeled `TW11 (K)` source values remain excluded from active use and are preserved only for provenance in `validation_data/validation_cases.csv`.