---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_contract_interpretation.csv
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_heat_ledger.csv
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv
  - work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/summary.json
tags: [forward-model, boundary-modeling, heater-source, paper-methods]
related:
  - .agent/status/2026-07-14_AGENT-390.md
  - work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/README.md
task: AGENT-390
date: 2026-07-14
role: BC-modeling/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# Heater Fraction / Forward-v1 Paper Methods

## Observed Facts

The existing heater/test-section source contract provides per-case linearized
Tmean response to source perturbations for Salt2, Salt3, and Salt4. The current
split is Salt2 train, Salt3 validation, and Salt4 holdout.

The new package fits at most one source scalar on Salt2:

- `eta_heater = 0.989703290269`;
- or `test_section_external_loss_W = 2.7358357756 W`.

Held-out mean absolute Tmean error:

- heater-only unfitted: `5.75251337999 K`;
- Salt2-fitted `eta_heater`: `3.19933235494 K`;
- Salt2-fitted test-section external loss: `3.61218425732 K`;
- legacy 37 W test-section source: `34.6987601706 K`.

## Interpretation

Heater-only is the safest unfitted source contract for the next setup-only
boundary/HX work. The 37 W direct test-section fluid source is rejected as the
default current source contract because it has the wrong sign relative to the
current evidence and much worse held-out error.

The Salt2-only one-scalar candidates are useful calibration candidates, but they
do not admit final forward-v1. The evidence still sits inside the imposed-cooler
forward-v0 context, so the next gate is setup-only cooler/HX modeling, not a
final paper claim of predictive thermal closure.

## Guardrails

The builder uses no CFD `mdot`, no realized CFD `wallHeatFlux`, no imposed CFD
cooler duty as a final predictive HX input, and no validation/holdout
temperature refit. Realized heater/test-section wall heat remains diagnostic
only.

## Files Produced

- `tools/analyze/build_heater_fraction_forward_v1_paper_methods.py`
- `tools/analyze/test_heater_fraction_forward_v1_paper_methods.py`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/methods_process.md`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/heater_fraction_scalar_candidates.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/heater_fraction_split_scores.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/heater_fraction_model_summary.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/heater_fraction_decision_table.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/runtime_input_audit.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/result_intake_table.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/claim_limitations_table.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/figure_table_index.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/source_manifest.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/summary.json`

## Validation

```text
python3.11 -m unittest tools.analyze.test_heater_fraction_forward_v1_paper_methods

Ran 5 tests in 0.046s
OK
```

## Recommended Next Action

Claim `BCM-COOLER-HX-UA-V1` or an equivalent Fluid-owned boundary/HX row next.
The heater/source contract is now split-aware enough to carry into that work;
the unresolved first-order thermal boundary is still setup-only cooler/HX
removal.
