---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_results.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_segment_states.csv
  - work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv
tags: [thermal-parity, forward-model, heat-loss, thesis-source]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/README.md
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-356
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Best Predictive Heat-Loss Discrepancy

## Open First

1. `presentation_brief.md` — one-page meeting/presentation version.
2. `best_predictive_leg_heat_loss_discrepancy.csv` — main numerical table.
3. `model_change_recommendations.csv` — what to change in the 1D model.
4. `repeatability_and_refinement_guide.md` — how to rerun and reuse after model
   updates.
5. `thesis_reuse_index.md` — thesis/presentation wording and claim boundaries.

## Model Compared

The comparison uses `solve_case` `F1_heater_only` as the best current
predictive-style thermal model: heater-only source with imposed cooler duty.
This is the current best executable model for this comparison, but it is not a
final predictive HX closure because it still consumes imposed cooler duty.

## Main Result

Aggregate heat balance is much closer than the leg-by-leg heat-loss
distribution. The model over-loses heat in the cooling branch, downcomer, lower
leg, and upcomer, while it strongly under-loses heat in the junction/stub
connector lane.

The key table is `best_predictive_leg_heat_loss_discrepancy.csv`. The short
presentation finding is: **the current model's total heat balance looks close
because pipe-leg over-loss cancels junction/stub under-loss.**

## Case Summary

- `salt_2`: model total loss `265.701 W`, CFD realized total loss `243.393 W`, largest discrepancy `junction:-35.694251959374995`.
- `salt_3`: model total loss `297.501 W`, CFD realized total loss `272.869 W`, largest discrepancy `junction:-39.328731678156`.
- `salt_4`: model total loss `337.601 W`, CFD realized total loss `310.408 W`, largest discrepancy `junction:-43.98897682842`.

## Model-Change Summary

- `lower_leg` (high): mean model-minus-CFD-realized loss = 28.693 W; largest absolute case = salt_4 (32.95595543358 W).
- `upcomer` (medium): mean model-minus-CFD-realized loss = 16.099 W; largest absolute case = salt_2 (17.687848473129996 W).
- `cooling_branch` (medium): mean model-minus-CFD-realized loss = 10.408 W; largest absolute case = salt_4 (12.364063289539985 W).
- `downcomer` (medium): mean model-minus-CFD-realized loss = 9.182 W; largest absolute case = salt_4 (11.542204068639997 W).
- `junction` (high): mean model-minus-CFD-realized loss = -39.671 W; largest absolute case = salt_4 (-43.98897682842 W).

## Repeatability

Regenerate the package from repo root with:

```bash
python3.11 tools/analyze/build_best_predictive_heat_loss_discrepancy.py
python3.11 -m unittest tools.analyze.test_best_predictive_heat_loss_discrepancy
```

The script consumes only existing work-product CSVs and writes only this package
directory. It does not run OpenFOAM, touch scheduler state, mutate native CFD
outputs, or edit external Fluid source.

## Files

- `best_predictive_leg_heat_loss_discrepancy.csv`
- `best_predictive_case_heat_loss_summary.csv`
- `model_change_recommendations.csv`
- `presentation_brief.md`
- `repeatability_and_refinement_guide.md`
- `thesis_reuse_index.md`
- `methodology.md`
- `thesis_notes.md`
- `source_manifest.csv`
- `summary.json`
- `README.md`
