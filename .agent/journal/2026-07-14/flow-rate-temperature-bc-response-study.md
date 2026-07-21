# Flow Rate, Temperature, and Boundary-Condition Response Study

Task: `AGENT-351`
Date: `2026-07-14`

Implemented a chart-first study package joining case-level setup BCs, time-series
mdot/temperature aggregates, patch-role boundary reductions, submitted-run
steady labels, corrected-Q harvest status, and false-steady perturbation
provenance.

Key guardrails: old Q perturbation rows are invalid_false_steady provenance;
corrected-Q +/-5 rows harvested by job 3295437 are terminal but split/BC-role
pending; radiation is embedded in `rcExternalTemperature` wallHeatFlux with no
separate exported `qr`.

AGENT-359 hardening added paper-ready trend/regression descriptors, split-aware
corrected-Q +/-5 overlays from AGENT-353, conclusion rows, and a generated
paper narrative without changing solver outputs or admission state.
