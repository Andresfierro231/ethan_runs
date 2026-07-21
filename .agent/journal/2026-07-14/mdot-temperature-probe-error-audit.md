# mdot / TP-TW Probe Error Audit

Task: `AGENT-360`
Date: `2026-07-14`

Implemented a reproducible Salt1-4 1D model assessment package. The study
compares pressure-root mdot errors with TP/TW probe errors for full CFD heat
flux, heater/test/cooler, and heater/cooler modes, then separately scores
cooling-leg heat removal and heating-leg heat addition model forms.

Guardrails: Salt1 remains diagnostic/context only; Salt2/Salt3/Salt4 keep
train/validation/holdout labels; realized CFD wallHeatFlux modes are
CFD-informed diagnostics; fixed-mdot modes are thermal isolation diagnostics;
rcExternalTemperature radiation is embedded in wallHeatFlux with no separate
exported qr term.
