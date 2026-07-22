---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/hybrid_1d_model_contract.csv
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/13_two_tap_recirc_section_effective_pressure_model.md
tags: [recirculation, exchange-cell, reduced-model, pressure-ledger, thermal-modeling]
related:
  - .agent/status/2026-07-21_TODO-LITREV-THROUGHFLOW-RECIRC-EXCHANGE-CELL.md
  - .agent/journal/2026-07-21/litrev-throughflow-recirc-exchange-cell.md
task: TODO-LITREV-THROUGHFLOW-RECIRC-EXCHANGE-CELL
date: 2026-07-21
role: Thermal-modeling/Hydraulics/Implementer/Writer
type: work_product
status: complete
---
# LitRev Throughflow Recirculation Exchange-Cell Design

## Decision

Use three reduced-model modes, selected by topology and recirculation evidence:

1. `one_stream_developing`: use the ordinary one-stream branch model only when
   signed net throughflow is stable and local reverse-flow diagnostics are below
   TAMU-calibrated tolerances.
2. `signed_flow_junction_network`: use a signed-flow path network only when a
   discrete modeled branch or junction path has negative net mass flow or a
   reproducible path pressure reversal.
3. `throughflow_recirc_exchange_cell`: use a main throughflow lane plus an
   explicit recirculation/exchange cell when net branch throughflow still exists
   but persistent local reverse area/mass or a coherent stagnant volume
   invalidates a single bulk state.

Current evidence supports this as an interface design only. No threshold,
coefficient, component `K`, `f_D`, `Nu`, F6, exchange rate, or pressure/energy
penalty is admitted here.

## Model Interface

The dry interface is defined in `model_interface_contract.csv`. The mandatory
recirculation-cell fields are:

- `R_mu`: viscosity ratio between the recirculation-cell reference state and
  main-throughflow reference state.
- `R_rho`: density ratio between the recirculation-cell reference state and
  main-throughflow reference state.
- `V_recirc`: coherent recirculating volume assigned to the cell.
- `mdot_exchange`: bidirectional exchange mass-flow magnitude between the main
  stream and the recirculation cell.
- `T_recirc`: cell bulk temperature.
- `pressure_residual`: pressure residual left after hydrostatic, kinetic,
  straight, development, and admitted junction/component terms are separated.
- `energy_residual`: heat/enthalpy residual left after main throughflow,
  wall/source/sink terms, and exchange terms are separated.

`tau_recirc = rho_recirc * V_recirc / mdot_exchange` is carried as a derived
residence time when the denominator is finite. If `mdot_exchange` is missing or
near zero, the row remains diagnostic instead of emitting an extreme time scale
or fitted coefficient.

## Residual Equations

The pressure and energy residual definitions are in
`residual_equation_contract.md`. They intentionally separate residual targets
from future closures. The design exposes the residuals for later calibration;
it does not hide them inside a global friction or heat-transfer multiplier.

## Required Evidence

`cfd_evidence_requirements.csv` lists the minimum CFD or postprocessed evidence
needed before a row can move beyond dry design. The shortest critical list is:
same-window signed mass flux, `RAF`, `RMF`, `SVF`, static/`p_rgh` pressure
basis, kinetic correction, straight/development subtraction, wall/source heat
terms, bulk and recirculation temperatures, recirculation volume support, mesh
or time uncertainty, split-safe score status, and runtime-input legality.

## Failure Criteria

The failure criteria in `failure_criteria.csv` keep this lane conservative.
Rows fail to diagnostic-only status if topology indicates a signed-flow network
instead, if the recirculation volume cannot be identified, if denominator terms
are near zero, if same-window pressure/thermal fields are missing, if mesh/time
uncertainty is absent for admission, or if a proposed implementation uses held
out CFD outputs as runtime inputs.

## Handoff

The future Fluid/API handoff should add a disabled-by-default exchange-cell
interface that accepts the fields in `model_interface_contract.csv` and returns
named pressure and energy residual ledger terms. It should not fit coefficients
or select switching tolerances until the separate switching-calibration and
split-safe scoring tasks admit those values.

## Files

- `switching_model_selection_contract.csv`
- `model_interface_contract.csv`
- `cfd_evidence_requirements.csv`
- `failure_criteria.csv`
- `residual_equation_contract.md`
- `source_manifest.csv`
- `summary.json`
