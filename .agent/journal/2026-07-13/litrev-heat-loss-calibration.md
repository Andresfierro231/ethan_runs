# Lit-Rev Heat-Loss Calibration

Date: `2026-07-13`

Task: `TODO-LITREV-HEAT-LOSS-CALIBRATION`

Built a separated heat-loss package with 207 heat-path rows and 18 admission
rows. The ledger separates cooler/jacket removal, passive convection,
rcExternalTemperature radiation metadata, heater input, wall/storage unknowns,
and residual.

Interpretation: internal Nu must not absorb passive, jacket, radiation, heater
efficiency, or storage residuals. Radiation remains inseparable from realized
wallHeatFlux until a distinct term is observed or bounded independently.

Recommended next action: use `heat_closure_admission.csv` as a guardrail before
any internal HTC/Nu calibration.

