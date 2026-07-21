---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_split_policy_section.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_current_context.md
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion/README.md
tags: [thesis-section, current-section, split-policy, evidence-classes]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
task: AGENT-502
date: 2026-07-17
role: Writer
type: thesis-section
status: current-draft
supersedes:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_split_policy_section.md
superseded_by:
---
# Split Policy And Evidence Classes

## Purpose

The split policy defines which rows may train or calibrate model terms and
which rows are reserved for scoring. It prevents CFD replay, calibration, and
prediction from being mixed.

## Final Predictive Split

| Role | Rows | Use |
| --- | --- | --- |
| final training | `salt1_nominal`, `salt2_jin_nominal`, `salt3_jin_nominal`, `salt4_nominal` | Fit or calibrate admitted final model terms. |
| training support | `salt1_lo10q`, `salt1_hi10q`, `salt4_lo5q`, `salt4_hi5q` | Support sensitivity and trend checks with labels preserved. |
| holdout/testing | `salt2_lo5q`, `salt2_hi5q` | Score prediction only; no fitting, tuning, or model selection. |
| external test | `val_salt2` | External score after matching heat-loss and admission package. |
| future holdout candidates | Salt2/Salt4 +/-10Q | Candidate testing rows after terminal harvest and admission. |
| new-CFD holdout candidates | Salt3 Q x insulation/onset matrix | Candidate testing rows after staging, completion, and admission. |

Older Salt2-train, Salt3-validation, Salt4-holdout language remains dated
method-development context. It is not the final thesis split.

## Evidence Classes

| Class | Meaning |
| --- | --- |
| Training | May fit or calibrate a final model term. |
| Training support | May guide trends and bounded checks, with special labels preserved. |
| Holdout/testing | May score a frozen model; may not fit, tune, or select it. |
| External test | Held outside the training/support family for external scoring. |
| Diagnostic | Explains model-form error but is not a final predictive input or fit row. |
| Blocked | Cannot support the intended claim until a named blocker is resolved. |

The class applies to both case rows and quantities. A case can be legal for
holdout scoring while a particular pressure or thermal coefficient from that
case remains diagnostic because of recirculation, heat-balance residual,
pressure-plane ambiguity, or mesh uncertainty.

## Runtime Leakage Rule

A final predictive model may not use validation outputs as inputs. Prohibited
runtime inputs include:

- CFD mass flow rate;
- realized CFD `wallHeatFlux`;
- imposed CFD cooler duty;
- validation TP/TW or branch temperatures;
- pressure losses measured from the row being scored;
- heat or pressure coefficients fit using the row being scored.

These quantities may be used in replay studies. Replay studies diagnose missing
physics; they do not establish final predictive performance.

## Scorecard Contract

Final scorecards should report:

- mass-flow error;
- pressure residual and movement by branch/segment;
- mean temperature error;
- loop temperature-difference error;
- TP/TW sensor error with sensor-map caveats;
- heater, cooler, passive wall, test-section, junction, and residual heat
  lanes;
- uncertainty and admission status.

A single scalar error is not sufficient. A model can improve temperature RMSE
for the wrong physical reason if heat placement or mass flow is wrong.

## Admission Before Use

A row enters the split only after admission checks pass. Terminal availability
or final-window data is not enough by itself. The row must also be compatible
with the specific model term being fit or scored. Recirculating upcomer rows,
for example, can support recirculation diagnostics but not ordinary
single-stream `Nu`, `f_D`, or component `K` fits.
