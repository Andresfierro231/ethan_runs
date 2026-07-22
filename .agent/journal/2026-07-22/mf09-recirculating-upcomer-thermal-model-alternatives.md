---
provenance:
  generated_by: tools/analyze/build_mf09_recirculating_upcomer_thermal_model_alternatives.py
  task_id: TODO-MF09-RECIRCULATING-UPCOMER-THERMAL-MODEL-ALTERNATIVES-2026-07-22
  generated_at_utc: 2026-07-22T14:05:58.225544+00:00
task: TODO-MF09-RECIRCULATING-UPCOMER-THERMAL-MODEL-ALTERNATIVES-2026-07-22
tags:
  - journal
  - MF09
  - recirculating-upcomer
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives
---

# MF09 recirculating-upcomer thermal model alternatives

## Attempted

Compared four predeclared alternatives: guarded ordinary-upcomer exclusion,
throughflow-plus-recirculation exchange cell with signed wall heat, two-zone
stratified mixed-convection upcomer, and source-side energy residual bridge.

## Observed

Temporal UQ exists for the proxy S13 exchange QOIs, but same-label mesh/GCI has
0 accepted rows. Source/property conservation is not released, ordinary internal
Nu fit rows are 0, exchange-cell fit-ready rows are 0, and onset anchor rows are
0.

## Inferred

The exchange-cell model is the highest-value physical lane, but it is not
smoke-ready. The current result should be used to define the missing QOIs and
source/property work, not to fit a coefficient or force ordinary upcomer closure.

## Contradictions or Caveats

Pressure support remains support evidence only; it is not component-K/F6
admission. Source-side heat remains source-side and must not be relabeled as
direct wall heat. Heat residuals must remain explicit instead of being absorbed
into internal Nu.

The heat-flow match check makes the same point numerically: with the current
diagnostic exchange scale, matching wall or source-side heat would require
unphysical cp-scale values. The right next step is same-mask `T_recirc`,
`T_core`, and property harvest after mesh/GCI and source/property gates pass.

## Next Useful Actions

Complete same-label mesh-family generation for Qwall/exchange-cell QOIs, then
repeat mesh/GCI/source-property gates before any exchange-cell train-only smoke
test.
