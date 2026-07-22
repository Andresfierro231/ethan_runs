---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/diagnostic_average_exchange_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/missing_gate_matrix.csv
tags: [journal, s13, upcomer-exchange, diagnostic-average, thermal-reduction]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-AVERAGE-FIELD-THERMAL-REDUCTION-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/README.md
task: TODO-S13-UPCOMER-EXCHANGE-AVERAGE-FIELD-THERMAL-REDUCTION-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
---
# S13 Upcomer Exchange Average Field Thermal Reduction

Observed: the seeded surface/input manifest supplies Salt2/Salt3/Salt4 recirc
masks, interface face lists, cell VTK paths, volume CSVs, source/sink values,
and a seeded-CV outward normal convention.

Observed: the whole-mesh cell VTKs contain `cellID`, `U`, `T`, and `rho`. They
do not release pressure, viscosity, wallHeatFlux, or `cp` fields for admission.

Attempted: implemented a streaming VTK reduction keyed by explicit `cellID`,
computed volume-weighted seeded-CV averages, computed interface owner/core
area averages, and read native OpenFOAM face vectors to form a signed outward
mass-flux proxy without launching a solver, sampler, or extractor.

Observed: all three cases reduce successfully. The proxy shows increasing
positive outward exchange support across Salt2/Salt3/Salt4
(`2.68592194714e-05`, `4.23665968058e-05`, `7.65896288069e-05 kg/s`) and
decreasing `tau_recirc_proxy` (`868.807159089`, `547.838912867`,
`301.390653047 s`).

Inferred: the diagnostic averages give S13/S12 a finite heat-path context and
identify useful magnitudes for later sampled-field work, but they do not replace
sampled wall/interface fields or same-QOI UQ.

Caveat: `hA_source_side_proxy_W_K` uses source/sink context and the diagnostic
seed/core temperature contrast. It is not a wallHeatFlux-derived `Q_wall_W`
integration and must not be admitted as a closure coefficient.

Next useful action: move to the trigger-gated S13 sampled-field/Qwall/UQ unblock
row. That row should decide whether limited sampled interface `U/T/rho`,
wall/core `T`, and eventually `Q_wall_W` evidence can be produced or must remain
fail closed.
