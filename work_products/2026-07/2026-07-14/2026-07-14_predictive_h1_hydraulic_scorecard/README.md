---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/forward_v0_hydraulic_residuals.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv
tags: [forward-model, predictive-1d, hydraulics, h1-proxy, scorecard]
related:
  - .agent/status/2026-07-14_AGENT-310.md
  - .agent/journal/2026-07-14/predictive-h1-hydraulic-scorecard.md
task: AGENT-310
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Predictive H1 Hydraulic Scorecard

This package scores the bounded AGENT-308 H1 fixed-K proxy against the prior hydraulic gate. It performs no thermal fitting, does not edit external Fluid source, and does not mutate native CFD outputs.

## Decision

- H1 passes the directional hydraulic screen for `F1_heater_only`: mean mdot error drops from `0.005478` kg/s to `0.002144` kg/s, a `60.29%` reduction.
- The remaining mean H1 mdot error is `14.42%` of CFD mdot, and all H1 rows still overpredict CFD mdot.
- This is enough to unblock a forward-v1 scorecard refresh as diagnostic/proxy hydraulic evidence.
- This is not enough to claim a final localized H1 closure or publication-ready forward-v1 model; current Fluid support only exercised one aggregate fixed-K proxy.

## Train / Diagnostic Boundary

- `salt_2` is the training residual because the proxy K was trained from Salt2 finite fit-target rows.
- `salt_3` is a validation diagnostic check with no refit.
- `salt_4` is a holdout diagnostic check with no refit.
- No validation or holdout rows were used to train K, and no thermal response was fitted.

## Outputs

- `h1_hydraulic_scorecard.csv`
- `h1_variant_decision_summary.csv`
- `hydraulic_term_boundary.csv`
- `source_manifest.csv`
- `summary.json`

## Reproduce

```bash
python3 tools/analyze/build_predictive_h1_hydraulic_scorecard.py
python3 -m unittest tools.analyze.test_predictive_h1_hydraulic_scorecard
```
