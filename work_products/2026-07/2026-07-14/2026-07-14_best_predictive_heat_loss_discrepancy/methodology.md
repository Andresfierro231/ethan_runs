# Methodology

## Leg Aggregation

Fluid `solve_case` segment states for `F1_heater_only` are aggregated into the
same five comparison groups used by the CFD heat ledger:

- `lower_leg`: heated incline.
- `upcomer`: left lower vertical, test section, and left upper vertical.
- `cooling_branch`: cooled incline pre-HX, active HX, and post-HX.
- `downcomer`: right vertical.
- `junction`: top/bottom horizontal connectors and junction-adjacent pieces.

For each leg:

```text
model_total_loss = Q_hx_sink + Q_ambient
model_net_to_fluid = Q_source - Q_hx_sink - Q_ambient
loss_discrepancy = model_total_loss - CFD_realized_loss
```

Positive loss discrepancy means the 1D model loses too much heat from that leg.
Negative means the 1D model does not lose enough heat from that leg.

## Inputs

- Model leg losses: `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_segment_states.csv` filtered to `engine=solve_case`
  and `variant_id=F1_heater_only`.
- Model case totals and source contract: `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_results.csv`.
- CFD realized/imposed heat by comparison leg: `work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv`.
- Prior full diagnostic heat-path alignment: `work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/heat_loss_alignment_by_segment.csv`.
- Model-change guardrails: `work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv`.

## Output Semantics

- `model_total_loss_W = model_hx_loss_W + model_ambient_loss_W`.
- `model_minus_cfd_realized_loss_W > 0`: 1D loses too much heat from that leg.
- `model_minus_cfd_realized_loss_W < 0`: 1D loses too little heat from that leg.
- `model_minus_cfd_realized_net_W` keeps source placement visible so heater
  over-input and wall-loss errors cannot cancel silently.

## Guardrails

This is a predictive-style discrepancy audit, not a new closure fit. The model
uses imposed cooler duty, so the package is not final predictive-HX evidence.
Realized CFD `wallHeatFlux` is used only as a comparison target. CFD mdot,
realized `wallHeatFlux`, and validation temperatures are not admitted as
runtime predictive inputs.

## Updating After 1D Refinement

When a new 1D model variant lands, rerun or clone this package with the new
variant ID in `BEST_VARIANT`, confirm the leg aggregation still maps every Fluid
parent segment, and compare the new `model_change_recommendations.csv` against
this package. A useful refinement should reduce the junction under-loss without
creating a larger pipe-leg over-loss or using forbidden runtime targets.
