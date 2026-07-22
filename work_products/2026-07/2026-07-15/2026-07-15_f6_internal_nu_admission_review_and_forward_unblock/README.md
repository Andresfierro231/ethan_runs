---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/resampled_pm5_matched_plane_metrics.csv
  - work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation/thermal_internal_nu_admission_review.csv
  - work_products/2026-07/2026-07-15/2026-07-15_downstream_pm5_final_state_refresh/f6_pm5_row_readiness.csv
  - work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification/hydraulic_admission_final_decisions.csv
tags: [f6, internal-nu, hydraulic, forward-v1, admission]
related:
  - operational_notes/maps/friction-closures.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-425
date: 2026-07-15
role: Coordinator/Hydraulics/Internal-Nu/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6/Internal-Nu Admission Review And Forward Unblock

## Result

This package answers the current unblock question from existing evidence only.
The repaired PM5 wall-band VTK state unlocks review, not final admission.

- PM5 rows reviewed: `12`.
- PM5 rows with wallHeatFlux: `12`.
- F6 fit-admissible rows now: `0`.
- Internal-Nu fit-admissible rows now: `0`.
- Positive local `h_proxy` rows: `8`.
- Segment sign/heat-balance pass rows: `0`.
- Final forward-v1 status: `blocked_no_go_final_forward_v1_not_admitted`.
- Final hydraulic residual status: `blocked_not_final`.

## Interpretation

Yes, repaired wall-band `wallHeatFlux` can be used to compute
`h_proxy = q''/(Twall - Tbulk)` for diagnostic review. It cannot by itself
admit internal Nu. Rows must still pass sign convention, wallHeatFlux-vs-
enthalpy heat balance, recirculation, mesh/time, and residual-ownership gates.

Current PM5 rows remain diagnostic/section-effective because reverse mass is
material and Ri is strongly mixed-convective. Rows with positive `h_proxy` are
useful diagnostics, but not single-stream fitted Nu rows. Rows with negative
`h_proxy` under the current sign convention require sign review before even
diagnostic interpretation beyond the local calculation.

## Recommended Next Run/Edit

1. Do not run a final forward-v1 scorecard from these rows yet.
2. Use `f6_onset_scorecard.csv` as pressure/onset diagnostic evidence only.
3. Resolve the thermal sign/heat-balance gate before Nu fitting.
4. To move past recirculation for true coefficients, obtain non-recirculating or
   near-transition matched-plane/pressure rows, or explicitly create a separate
   bidirectional/section-effective closure path with its own admission gate.

No native CFD solver outputs, registry/admission state, scheduler state,
generated indexes, or external Fluid code were mutated.

## Outputs

- `f6_onset_scorecard.csv`
- `f6_fit_candidate_table.csv`
- `internal_nu_h_proxy_review.csv`
- `thermal_sign_heat_balance_gate.csv`
- `internal_nu_admission_decision.csv`
- `final_forward_v1_unblock_requirements.csv`
- `source_manifest.csv`
- `summary.json`
