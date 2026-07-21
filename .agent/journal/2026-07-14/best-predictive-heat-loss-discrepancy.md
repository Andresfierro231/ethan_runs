---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_results.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_segment_states.csv
  - work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv
  - work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/summary.json
tags: [thermal-parity, forward-model, heat-loss, methodology, thesis-source]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/README.md
  - reports/thesis_dossier/README.md
task: AGENT-356
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Best Predictive Heat-Loss Discrepancy

## Why This Exists

The user asked to compare, for each Salt case, the discrepancy in heat loss for
the current best predictive model: which leg loses heat, how different it is
from CFD, and what model changes are needed to better match CFD.

## Model Compared

I used `solve_case` `F1_heater_only` from the forward-v0 confirmation package.
This is the current best predictive-style thermal model because it removes the
37 W test-section source and uses heater-only source with imposed cooler duty.
It is not final predictive-HX evidence because imposed cooler duty is still a
runtime shortcut.

## Method

Fluid segment states were aggregated into five CFD-comparable legs:
`lower_leg`, `upcomer`, `cooling_branch`, `downcomer`, and `junction`.

For each leg:

```text
model_total_loss = Q_hx_sink + Q_ambient
loss_discrepancy = model_total_loss - CFD_realized_loss
```

Positive discrepancy means the 1D model loses too much heat from that leg.
Negative discrepancy means the model does not lose enough.

## Result

The aggregate heat balance is close in all three Salt cases, but that closeness
is not a reliable model-form success. It is cancellation:

- lower leg over-loss averages about 28.7 W;
- upcomer/test-section over-loss averages about 16.1 W;
- cooling branch over-loss averages about 10.4 W;
- downcomer over-loss averages about 9.2 W;
- junction/stub/horizontal connector under-loss averages about 39.7 W.

The highest-priority model changes are therefore:

1. Add junction/stub/horizontal connector heat-loss coverage.
2. Separate heater realization from lower-leg wall loss so cancellation does
   not masquerade as model agreement.
3. Keep active HX/cooler separate from passive upper-leg wall loss and replace
   imposed cooler duty with a setup-only UA/effectiveness model.
4. Implement wall/shell/external-boundary drive for upcomer and downcomer
   losses.

## Guardrails

Do not use realized CFD `wallHeatFlux`, CFD mdot, or validation temperatures as
predictive runtime inputs. They are comparison targets here. Salt3/Salt4 should
remain validation/holdout scoring rows for any fitted boundary parameter.
