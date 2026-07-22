# Patch-Boundary Fixed-mdot 1D Parity

Generated: `2026-07-13T17:41:30+00:00`
Task: `AGENT-271`

## Purpose

This package converts the AGENT-263 CFD patch boundary ledger into 1D segment
inputs and applies the AGENT-264 rcExternalTemperature radiation decision. It
keeps the external Fluid solver read-only. Executed modes are fixed-Q thermal
diagnostics at CFD mdot, not predictive hydraulic scores.

## Outputs

- `parity_input_contract.csv`: CFD segment-to-Fluid mapping with realized and imposed heat terms plus h/Ta/Tsur/emissivity metadata.
- `section_heat_balance.csv`: role-level patch sums by 1D segment.
- `run_plan.csv`: executable and non-executable parity modes.
- `fixed_mdot_parity_results.csv`: executed fixed-mdot results for B0-B3.
- `path_summary.csv`: thermal error and diagnostic pressure residuals by path.
- `parity_decision_table.csv`: radiation and external-BC implementation decisions.
- `run_metadata.json`: input paths, command, host, git revisions, and row counts.

## Scientific Boundary

Positive `realized_wallHeatFlux_W` means heat enters the fluid; negative means
heat leaves the fluid. The B2 realized-wallHeatFlux mode therefore treats
positive segment sums as prescribed sources and negative segment sums as
prescribed losses. AGENT-264 concluded that `rcExternalTemperature` emissivity
and `Tsur` affect heat flux, but no separable radiation ledger is exported.
Therefore this package does not add a separate 1D radiation term on top of CFD
wallHeatFlux.

`B4_external_bc_equivalent_contract` is intentionally not executed. The current
repo-local Fluid API can prescribe segment sources/losses, but does not accept
patch-level or segment-level h/Ta/Tsur/emissivity/layer boundary dictionaries.
A later Fluid-owned task should implement that combined external boundary if
temperature-dependent parity is required.

## Key Counts

- Contract rows: `15`
- Section heat-balance rows: `24`
- Run-plan rows: `15`
- Result rows: `12`
- Best executed path by mean absolute Tmean error: `B1_legacy_cfd_cooler_duty`
