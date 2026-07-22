---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/paper_methods_pressure_basis.md
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/hybrid_model_candidate_contract.csv
tags: [recirculation, exchange-cell, residual-contract, pressure-ledger, thermal-modeling]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/README.md
task: TODO-LITREV-THROUGHFLOW-RECIRC-EXCHANGE-CELL
date: 2026-07-21
role: Thermal-modeling/Hydraulics/Implementer/Writer
type: work_product
status: complete
---
# Residual Equation Contract

## State Split

The exchange-cell model has a main throughflow control volume and one local
recirculation cell:

```text
main stream: mdot_main, T_main_in, T_main_out, p_main_in, p_main_out
cell:        V_recirc, T_recirc, rho_recirc, mu_recirc
exchange:    mdot_exchange, tau_recirc
```

`mdot_exchange` is a positive bidirectional exchange magnitude. At steady state,
the main-to-cell and cell-to-main exchange masses are equal, so the cell has no
net mass source.

## Property Ratios

```text
R_mu  = mu(T_recirc, property_mode)  / mu(T_main_exchange, property_mode)
R_rho = rho(T_recirc, property_mode) / rho(T_main_exchange, property_mode)
```

The reference `T_main_exchange` is the local main-stream exchange temperature.
A later implementation may choose inlet, outlet, or midpoint only if it records
that basis and uses the same basis for scoring.

## Residence Time

```text
tau_recirc = rho_recirc * V_recirc / mdot_exchange
```

If `V_recirc` or `mdot_exchange` is missing, or if `mdot_exchange` is near zero,
the row emits a diagnostic missing-denominator status. It does not emit an
extreme residence time or fit a compensating coefficient.

## Pressure Residual

The model target is a named residual, not an ordinary component coefficient:

```text
Delta_p_resid =
    Delta_p_rgh
  - Delta_p_kin
  - Delta_p_straight
  - Delta_p_dev
  - Delta_p_admitted_feature
```

`Delta_p_rgh` follows the downstream-minus-upstream sign convention already used
by the two-tap section-effective model. `Delta_p_admitted_feature` is zero
unless a separate row has admitted an isolated component or junction term on the
same pressure basis.

A future closure may predict `Delta_p_resid` from recirculation state fields
such as `RAF`, `RMF`, `SVF`, `R_mu`, `R_rho`, `V_recirc`, `tau_recirc`, `Ri`,
`Gz`, and geometry. This package does not select that function or fit any
coefficient.

## Energy Residual

The steady main-stream energy ledger is:

```text
energy_residual =
    mdot_main * cp_main * (T_main_out - T_main_in)
  - Q_wall_main
  - Q_source_main
  - Q_sink_main
  - mdot_exchange * cp_exchange * (T_recirc - T_main_exchange)
```

The recirculation-cell ledger is:

```text
cell_energy_residual =
    Q_wall_recirc
  + Q_source_recirc
  - Q_sink_recirc
  + mdot_exchange * cp_exchange * (T_main_exchange - T_recirc)
```

For a fully specified steady exchange cell, both residuals should be carried.
If only the combined section balance is available, report the combined
`energy_residual` with `cell_energy_residual=missing`. Do not absorb the
unresolved term into internal `Nu`.

## Admission Boundary

The residuals are dry targets until all of these are present on the same
window and basis: recirculation metrics, pressure decomposition, cell volume,
exchange estimator, wall/source heat ledger, property mode, split-safe runtime
audit, and same-QOI uncertainty.
