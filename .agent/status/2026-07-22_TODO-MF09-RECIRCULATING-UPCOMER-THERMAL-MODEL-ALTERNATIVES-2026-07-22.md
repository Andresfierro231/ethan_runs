---
provenance:
  generated_by: tools/analyze/build_mf09_recirculating_upcomer_thermal_model_alternatives.py
  task_id: TODO-MF09-RECIRCULATING-UPCOMER-THERMAL-MODEL-ALTERNATIVES-2026-07-22
  generated_at_utc: 2026-07-22T14:05:58.225544+00:00
task: TODO-MF09-RECIRCULATING-UPCOMER-THERMAL-MODEL-ALTERNATIVES-2026-07-22
tags:
  - status
  - MF09
  - recirculating-upcomer
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives
---

# TODO-MF09-RECIRCULATING-UPCOMER-THERMAL-MODEL-ALTERNATIVES-2026-07-22

## Objective

Evaluate recirculating-upcomer thermal model alternatives without forcing a
single-stream entrance/development correction or admitting ordinary upcomer
`Nu/f_D/K`.

## Outcome

Decision: `blocked_missing_mesh_gci_source_basis`. Variants evaluated: `4`.
Smoke-ready variants: `0`. Admission-ready
variants: `0`. Accepted same-label
mesh/GCI QOIs: `0`.

The best next science lane is
`MF09b_throughflow_plus_recirculation_exchange_cell_with_signed_wall_heat`, but it remains blocked by missing
same-label mesh/GCI, missing source/property and cp basis, and no production
same-window exchange-cell harvest. Ordinary upcomer `Nu/f_D/K` remains disabled.

Heat-flow matching remains a residual-contract problem. Direct `Q_wall_W` spans
`23.1161370708 to 28.1231837021` W, source-side static heat spans
`166.349260094 to 205.373184962` W, and forcing the current exchange
`mdot*DeltaT` scale to match `Q_wall_W` would require `cp` spanning
`2153209.39866 to 6054171.49912` J/kg/K.

## Changes Made

- Wrote variant comparison table.
- Wrote QOI availability and UQ/source/property status table.
- Wrote ordinary-upcomer disabled-reasons table.
- Wrote production/admission gate, next work queue, source manifest,
  heat-path guardrail snapshot, onset/source gap snapshot, README, summary,
  status, journal, and import manifest.
- Wrote heat-flow match case diagnostics and energy residual bridge contract
  tables to define the mismatch and sign convention without fitting.

## Validation

- `python3.11 -m py_compile tools/analyze/build_mf09_recirculating_upcomer_thermal_model_alternatives.py tools/analyze/test_mf09_recirculating_upcomer_thermal_model_alternatives.py` passed.
- `python3.11 -m unittest tools.analyze.test_mf09_recirculating_upcomer_thermal_model_alternatives` passed.

## Guardrails

- Production harvest: false.
- Mesh/GCI execution: false.
- Scheduler/solver/sampler launch: false.
- Fluid solve: false.
- Validation/holdout/external-test scoring: false.
- Fitting/tuning/model selection: false.
- Ordinary upcomer `Nu/f_D/K` admission: false.
- Qwall/source/property release, coefficient admission, final score: false.
- Native-output mutation, registry/admission mutation, Fluid/external edit,
  blocker-register change, and generated-index refresh before closeout: false.
- Source-side heat was not relabeled as `Q_wall_W`.
- Residual was not absorbed into internal Nu.
