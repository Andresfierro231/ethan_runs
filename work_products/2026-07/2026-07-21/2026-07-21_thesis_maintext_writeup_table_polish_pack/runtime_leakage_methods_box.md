---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_post_study_writing_refresh/thesis_writer_handoff.md
tags: [thesis, runtime-leakage, methods-box]
task: TODO-THESIS-MAINTEXT-WRITEUP-TABLE-POLISH-PACK-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Methods Box: Runtime Inputs Versus Diagnostic Evidence

| Category | Allowed thesis use | Forbidden predictive-runtime use |
| --- | --- | --- |
| Geometry and setup fields | Runtime model inputs when source-backed. | Fill missing setup fields from scored CFD response. |
| External boundary dictionary | Setup-facing heat-path model inputs. | Realized CFD `wallHeatFlux` as runtime heat loss. |
| CFD pressure and heat fields | Targets, diagnostics, residual ownership, admission gates. | Pressure/heat target from the scored row as a model input. |
| CFD mass flow | Score target or diagnostic reference. | Runtime `mdot` input for prediction. |
| TP/TW temperatures | Post-solve score targets and residual diagnostics. | Runtime temperature input, fit target, or model-selection signal. |
| Holdout and external rows | Post-freeze scoring only. | Fitting, tuning, model selection, or candidate choice. |

This separation is the difference between a CFD-informed reduced model and a
CFD replay. A row can explain a residual without being legal as a runtime
input.
