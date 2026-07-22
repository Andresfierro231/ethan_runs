---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_pm10_upcomer_anchor_admission/pm10_upcomer_anchor_classification.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/recirculation_feature_scorecard.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/recirc_residual_scorecard.csv
  - work_products/2026-07/2026-07-20/2026-07-20_umx1_fluid_intake_decision/decision_matrix.csv
tags: [recirculation, upcomer, corner, dry-scorer, model-form]
related:
  - .agent/status/2026-07-20_TODO-DIRECT-RECIRC-MODEL-FORMS-AND-DRY-SCORERS.md
  - .agent/journal/2026-07-20/direct-recirc-model-forms-and-dry-scorers.md
task: TODO-DIRECT-RECIRC-MODEL-FORMS-AND-DRY-SCORERS
date: 2026-07-20
role: Hydraulics/Thermal-modeling/Forward-pred/Coordinator/Implementer/Tester/Writer
type: work_product
status: complete
---
# Direct Recirculation Model Forms And Dry Scorers

## Decision

Freeze three direct recirculation research forms now: `UH1`, `CR1`, and `ROX1`. Keep the regime/onset classifier as the gate that decides when these forms apply. None of these forms admit ordinary `Nu`, `f_D`, `K`, or `F6` rows today.

## Frozen Forms

- `UH1`: upcomer throughflow pipe plus recirculating exchange cell.
- `CR1`: corner/two-tap recirculating section-effective pressure residual.
- `ROX1`: reduced-order exchange/source term for a future Fluid substrate.

## Dry Scorers Implemented

- Upcomer dry rows: `10`.
- Corner residual dry rows: `3`.
- Regime gate rows: `10`.
- Frozen model forms: `3`.

The dry scorers report diagnostic severity and blocker status only. `fit_allowed_now=false` and `admission_allowed_now=false` are intentional outputs, not failures.

## Research Path

1. Use the literature review to choose nondimensional priors for `UH1` and `ROX1` rather than fitting recirculating rows as ordinary coefficients.
2. Use `regime_gate_dry_table.csv` as the admission gate for future high-heat or near-onset cases.
3. Use `corner_residual_dry_scorecard.csv` to track section-effective pressure residuals while keeping component `K` and `F6` blocked.
4. Re-score the same dry tables when terminal non-recirculating or near-onset anchors arrive.

## Active Blockers

- No non-recirculating or near-onset upcomer anchors are fit-admissible yet.
- Corner `q_ref` is still untrusted under material reverse flow.
- Same-QOI mesh/time uncertainty is missing for the corner residual lane.
- Current UMX1 exchange variants are not scorecard-ready.

## Generated Files

- `frozen_direct_recirc_model_forms.csv`
- `upcomer_hybrid_dry_scorecard.csv`
- `corner_residual_dry_scorecard.csv`
- `regime_gate_dry_table.csv`
- `research_avenue_assignments.csv`
- `next_steps_direct_recirc.csv`
- `source_manifest.csv`
- `summary.json`
