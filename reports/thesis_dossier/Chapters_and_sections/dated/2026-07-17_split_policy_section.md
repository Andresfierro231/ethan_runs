---
provenance:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_current_context.md
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/README.md
tags: [thesis-section, split-policy, prediction, training, holdout, validation]
related:
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_model_form_section.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_modeling_approach_section.md
  - reports/thesis_dossier/Outline.md
task: AGENT-497
date: 2026-07-17
role: Writer
type: thesis-section
status: draft
supersedes: []
superseded_by:
---
# Draft Thesis Section: Final Predictive Split Policy

## Section Role

This section belongs in the CFD case/admission chapter and again, in shorter
form, in the forward-predictive model chapter. Its purpose is to define which
CFD rows may be used to train or calibrate model terms, which rows may only
support model development, and which rows must be held out for testing. The
split policy is part of the scientific method: without it, diagnostic replay,
calibration, and prediction can be confused.

## Current Split

The current final predictive policy is:

| Role | Rows | Use |
| --- | --- | --- |
| final training | `salt1_nominal`, `salt2_jin_nominal`, `salt3_jin_nominal`, `salt4_nominal` | Fit or calibrate admitted final model terms. |
| training support | `salt1_lo10q`, `salt1_hi10q`, `salt4_lo5q`, `salt4_hi5q` | Support trend checks, sensitivity, and bounded closure decisions with labels preserved. |
| holdout/testing | `salt2_lo5q`, `salt2_hi5q` | Score prediction without fitting or tuning on these rows. |
| external test | `val_salt2` | External score only after matching heat-loss and admission package. |
| future holdout candidates | Salt2/Salt4 +/-10Q | Candidate testing rows after terminal harvest and admission. |
| new-CFD holdout candidates | Salt3 Q x insulation/onset matrix | Candidate testing rows after staging, completion, and admission. |

The older Salt2-train, Salt3-validation, Salt4-holdout split remains useful only
as dated method-development context. It should not be presented as the final
thesis split.

## Why The Split Changed

The split changed because the case inventory and admission state changed.
Salt1 nominal and perturbation rows are no longer context-only. They have been
schema-promoted or admitted as primary closure evidence with preserved q-ratio
labels and operational stop/cancel provenance. Salt2 and Salt4 perturbation rows
now provide more useful final testing and sensitivity structure than withholding
Salt4 nominal as the only canonical holdout.

The final training set therefore spans the admitted nominal Salt1-4 operating
states. This gives the model a broader nominal operating envelope while keeping
perturbation rows available to test whether the learned closure behavior
generalizes when heater power or related operating conditions are changed.

## Evidence Classes

The thesis uses five evidence classes:

| Class | Meaning |
| --- | --- |
| Training | A row may be used to fit or calibrate a final model term. |
| Training support | A row may guide trends, sanity checks, and bounded choices, but its special label must be preserved. |
| Holdout/testing | A row may be used for scoring only; no fitting, tuning, or model selection on this row. |
| External test | A row is held outside the training/support family and used for external scoring after admission. |
| Diagnostic | A row or mode explains model-form error but is not a legal predictive training or testing input. |

This classification applies to cases and to individual quantities inside a case.
For example, a case may be admitted as a holdout row while a particular pressure
or thermal coefficient inside that case remains diagnostic because of
recirculation, plane placement, heat-balance residual, or mesh uncertainty.

## Runtime Leakage Rule

The split policy must be paired with a runtime-input rule. A final predictive
model may not use validation outputs as inputs. In practical terms, the
following are prohibited as runtime inputs in thesis-strength predictive modes:

- CFD mass flow rate;
- realized CFD `wallHeatFlux`;
- imposed CFD cooler duty;
- validation TP/TW or branch temperatures;
- pressure losses measured from the row being scored;
- any coefficient fit or selected using the holdout or external-test row being
  scored.

These quantities can be used in replay studies. A replay study is valuable
because it diagnoses which physical submodel controls the error. It is not a
final prediction.

## Scoring Contract

Each final scorecard should report at least:

- mass-flow error;
- branch or segment pressure residual;
- mean temperature error;
- loop temperature-difference error;
- TP/TW sensor error, with sensor-map caveats;
- heat addition/removal by heater, cooler, passive wall, test section, and
  residual;
- uncertainty and admission status.

The main scalar error for a scorecard should not hide the decomposition. A lower
temperature RMSE can occur for the wrong physical reason if heat placement or
mdot is wrong. The scorecard must therefore preserve mass-flow, heat, pressure,
and sensor-temperature channels separately.

## Admission Before Split Use

A row enters the split only after it passes the relevant admission checks. These
include terminal or final-window availability, steady-state or oscillation
metrics, native-output provenance, mesh/reconstruction status where relevant,
and physical validity checks such as recirculation flags. A terminal CFD row is
not automatically a fit row. It must also be compatible with the coefficient or
model term being fit.

The upcomer illustrates this rule. Current evidence shows recirculating upcomer
behavior in key rows. Those rows can support a recirculation or onset story, but
they are not ordinary single-stream `Nu`, `f_D`, or component-`K` fit evidence.
The split policy does not override physical invalidity.

## Draft Thesis Wording

The final predictive split was defined to separate calibration from testing and
to prevent diagnostic CFD replay from being promoted into prediction. Admitted
nominal Salt1-4 rows form the final training set. Salt1 and Salt4 perturbation
rows provide labeled training support, while admitted Salt2 perturbation rows
are reserved for holdout testing. The `val_salt2` case is treated as an
external test after its heat-loss and admission evidence are matched to the
scorecard contract. Future Salt2/Salt4 +/-10Q rows and new CFD operating points
may expand the holdout pool only after terminal harvest and admission.

This split is quantity-aware. A case-level row may be legal for scoring while a
particular coefficient extracted from that row remains diagnostic or blocked.
The thesis therefore reports both row role and coefficient/admission status. The
final predictive model is evaluated only with setup inputs at runtime; CFD mass
flow, realized wall heat flux, imposed CFD cooler duty, validation temperatures,
and held-out pressure or heat targets are excluded from runtime use.
