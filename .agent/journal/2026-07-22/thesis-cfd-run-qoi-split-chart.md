---
provenance:
  - tools/analyze/build_thesis_cfd_run_qoi_split_chart.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_cfd_run_qoi_split_chart/summary.json
tags: [journal, thesis, cfd-qoi-chart, holdout-test]
related:
  - .agent/status/2026-07-22_TODO-THESIS-CFD-RUN-QOI-SPLIT-CHART-2026-07-22.md
task: TODO-THESIS-CFD-RUN-QOI-SPLIT-CHART-2026-07-22
date: 2026-07-22
role: Forward-pred / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Thesis CFD Run QoI Split Chart

## Attempted

Built an additive CFD QoI chart package for the thesis so model-training and
final-score tables can refer to one split-aware source for `mdot`, TP, and TW
targets.

## Observed

Existing evidence was distributed across the Salt1-4 postprocessing inventory,
the corrected Salt1 stopped-run/uncertainty package, the CFD legal-use matrix,
PM5 split admission matrix, defended sensor reference table, and the model-form
training roster. The Salt2/Salt3/Salt4 nominal, Salt2 +/-5Q, and external
validation rows have complete mdot/TP/TW coverage in the Salt1-4 inventory.
The latest corrected Salt1 source has mdot, TP probe values, and wall
temperature spatial mean, but not individual TW labels.

## Inferred

The external validation row can be reported inside a single protected
`holdout_test` bucket if its subtype remains `external_test`. This keeps the
thesis terminology simpler while preserving provenance and preventing use of
that row for fitting or model selection.

## Contradictions Or Caveats

The chart is a CFD target/diagnostic table only. It is not a runtime-input
table for the predictive 1D model. CFD mdot, TP, TW, realized wall heat flux,
post-solve cooler duty, and residual fills remain forbidden runtime inputs.

Salt1 individual TW values should not be inferred from the spatial wall mean.
The chart leaves those columns blank and records partial coverage.

## Next Useful Actions

Use `cfd_run_qoi_split_chart_wide.csv` as the thesis-facing run/QoI table and
as the split roster for future frozen-candidate scoring. Before fitting any
coefficients on Salt1-4 nominal rows, resolve the MF16 source/property
exact-field release blocker or document why training remains fail-closed.

## Guardrails

No protected scoring, fitting, model selection, source/property release,
Qwall release, coefficient admission, candidate freeze, solver/scheduler
action, native-output mutation, registry/admission mutation, or Fluid/external
edit occurred.
