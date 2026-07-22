---
provenance:
  task_id: TODO-S13-SEEDED-HEAT-PATH-LANE-RELEASE-2026-07-21
  generated_at: 2026-07-21T19:41:38-05:00
tags:
  - s13
  - upcomer
  - exchange-cell
  - heat-path
  - qwall-contract
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv/released_surface_vtk_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/case_preflight_matrix.csv
---

# S13 Seeded Heat-Path Lane Release

This package is a dry contract and fail-closed gate for the seeded upcomer
exchange-cell path.  It uses the released geometry-only exchange/wall VTKs,
seeded recirculation masks, whole-mesh cell VTK manifests, static source/sink
context, and the previous sampler/UQ gates.

## Outcome

- Geometry surfaces are present for Salt2/Salt3/Salt4.
- Whole-mesh cell VTKs contain `U`, `T`, `rho`, and `cellID` support.
- The package does not find `p`/`p_rgh`, `mu`/`nu`, `wallHeatFlux`, or
  `cp_J_kg_K` release.
- `Q_wall_W`, sampled interface fields, production harvest, same-window UQ,
  and coefficient/model admission remain blocked.

## Output Contract

- `field_inventory.csv`: available whole-mesh VTK fields.
- `sampled_field_lane_table.csv`: required sampled-field lanes and blockers.
- `qwall_contract.csv`: trusted-wall heat-flow convention and blocked state.
- `heat_path_lane_table.csv`: physical heat-path lanes and guardrails.
- `sampler_manifest_delta.csv`: updated sampler gaps after geometry VTK release.
- `harvest_readiness_gate.csv`: QOI-by-QOI readiness for `V_recirc`,
  `mdot_exchange`, `T_recirc`, `R_mu`, `R_rho`, pressure residual, and energy
  residual.
- `downstream_gate.csv`: allowed and forbidden next actions.

## Do Not Do

Do not treat geometry-only VTKs as sampled-field VTKs.  Do not substitute
`q_net_W` for `Q_wall_W`.  Do not absorb energy residual into internal Nu.  Do
not run sampler/harvest, fit coefficients, trigger S11/S12/S13/S15/S6, or make
strong claims before exact same-window QOI uncertainty exists.
