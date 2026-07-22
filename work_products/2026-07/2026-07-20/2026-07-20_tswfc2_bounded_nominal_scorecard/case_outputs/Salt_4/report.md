# Salt 4 — tswfc2_smoke_salt2_four_node_v1

## Summary

- Working fluid: `salt`
- Property set: `salt_jin`
- Mode: `predictive_airside_hx`
- Radiation: `False`
- Effective insulation thickness: `1.0` in
- Ambient temperature: `300.00` K
- Effective air flow: `37.00` L/min
- Effective air inlet temperature: `299.97` K
- Predicted air outlet temperature: `395.02` K
- Measured air outlet temperature: `406.11` K
- Predicted mass flow rate: `0.026964` kg/s
- Measured mass flow rate: `0.020100` kg/s
- Mass-flow error: `+0.006864` kg/s
- Predicted main-tube velocity: `0.037961` m/s
- Measured area-weighted mean velocity: `0.023700` m/s
- Velocity error: `+0.014261` m/s
- Predicted main-tube Reynolds number: `564.41`
- Buoyancy pressure: `32.2541` Pa
- Loss pressure: `32.2541` Pa
- Pressure residual |loss-buoyancy|: `0.000000` Pa
- Predicted HX duty: `63.5246` W
- Measured cooler duty: `65.9800` W
- Predicted ambient heat loss: `311.0759` W
- Temperature periodicity error: `-1.593889e-09` K
- Temperature scan bounds: `274.97` to `687.51` K
- Temperature scan expansions: `1`
- Temperature scan best endpoint side: `interior`
- Root status: `accepted`
- Accepted for validation metrics: `True`
- Validity status: `valid`
- Max bulk temperature: `589.13` K
- Minimum viscosity used in closure: `2.749790e-03` Pa·s
- Solver lineage: `scientific_reset_pre_revalidation_v1`
- Scientific trust policy: `2026-05-29_scientific_reset_v1`
- Paper admissibility: `not_paper_eligible_pending_revalidation`

## Validation Policy

- Validation data enter only in reporting. The active solver does not use measured TP/TW, measured mass flow, or measured HX duty as runtime inputs.
- `TW10` is reported separately as a cooling-jacket shell surrogate.
- The unlabeled `TW11 (K)` source values remain excluded from active use and are preserved only for provenance in `validation_data/validation_cases.csv`.