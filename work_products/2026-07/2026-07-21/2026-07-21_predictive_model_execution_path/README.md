---
provenance:
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - reports/thesis_dossier/Chapters_and_sections/current/07_wall_test_section_coupled_score_and_physics_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/07-26/20/2026-07-20_FORWARD_PREDICTIVE_BLOCKERS_AND_NEXT_STEPS.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
  - .agent/BLOCKERS.md
tags: [forward-model, predictive-1d, execution-path, fluid-walls, scorecard, litrev-synthesis]
related:
  - operational_notes/maps/forward-predictive-model.md
  - TODO-PRED-ENDTOEND-SCORE
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
task: TODO-PRED-ENDTOEND-SCORE
date: 2026-07-21
role: Forward-pred/Implementer/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Predictive Model Execution Path

## Objective

Build the shortest defensible path to a setup-only predictive model that
outputs loop `mdot`, branch temperatures, TP/TW sensor temperatures, and
pressure/thermal residual attribution.

This package is a plan and execution contract. It does not run Fluid, launch
OpenFOAM, fit coefficients, select a model, or admit a new closure.

## Current Baseline

The target model form is steady `fluid+walls`: each segment carries a fluid
state, wall/material stack, pressure slot, thermal circuit, source/sink role,
recirculation flag, admission status, and uncertainty status.

The current endpoint state is not a final prediction. The final scorecard shell
exists, but `FINAL_FREEZE_TBD` is still absent. Heater efficiency and cooler/HX
UA are no longer the broad blocker, but wall/test-section/passive-boundary
thermal shape remains open. Pressure corner/F6 work is diagnostic because
component isolation, same-QOI UQ, and material reverse-flow gates fail.

## Shortest Path

The path is staged so each lane can either admit a piece of the final model or
produce a scored diagnostic residual without contaminating the final split.

| Stage | Lane | Purpose | Exit condition |
| --- | --- | --- | --- |
| 0 | Baseline current model | Freeze the current legal baseline and scorecard schema before new model changes. | Baseline has a runtime audit, source/property labels, and declared missing predictions instead of silent gaps. |
| 1 | External BC dictionary | Make setup h/Ta/Tsur/emissivity/wall/layer/drive terms first-class runtime inputs. | Every segment/role has a dictionary row or an explicit missing/setup-unavailable label. |
| 2 | Pressure source-envelope lane | Convert LitRev pressure rules into coefficient labels and source-envelope gates. | Every pressure residual is named as straight, section, cluster, recirculation-effective, or residual; component K remains blocked unless isolation/recovery pass. |
| 3 | Heat-loss network lane | Build the thermal network without hiding heat residuals in internal Nu. | Heater, cooler, passive, test-section, junction/stub, radiation/external, storage, and residual lanes are separately scored. |
| 4 | Recirculation guard lane | Decide where single-stream branch closures are legal and where a hybrid exchange-cell path is required. | Ordinary `Nu`, `f_D`, and `K` fits are disabled for flagged upcomer/corner rows; hybrid terms have separate residual ledgers. |
| 5 | Frozen candidate and scorecard | Freeze one candidate and join predictions into the final scorecard shell. | Train/support/validation, holdout, and external-test claims are separate, with no held-out or external fitting/model selection. |

The machine-readable version is `staged_implementation_plan.csv`.

## Split Claims

The canonical final split remains:

| Claim class | Rows | Allowed claim |
| --- | --- | --- |
| Train/calibration | `salt1_nominal`, `salt2_jin_nominal`, `salt3_jin_nominal`, `salt4_nominal` | Fit admitted final terms and report training residuals. |
| Development validation/support | `salt1_lo10q`, `salt1_hi10q`, `salt4_lo5q`, plus predeclared within-training checks | Check sensitivity, robustness, and failure modes with labels preserved. These are not blind holdout claims. |
| Holdout/testing | `salt2_lo5q`, `salt2_hi5q` | Score a frozen model only. No tuning, fitting, or model selection. |
| External test | `val_salt2` | Score after freeze and after matching external heat-loss/admission package. No training reclassification. |
| Future external/holdout | Salt2/Salt4 +/-10Q and new CFD | Score only after terminal harvest, admission, and source/property release. |

The explicit matrix is `split_claim_boundaries.csv`.

## Residual Attribution

The final scorecard should report both prediction error and where the remaining
physics sits:

- pressure residuals: buoyancy-drive integral, straight/developing loss,
  section/cluster loss, corner/junction residual, recirculation-effective
  residual, and unresolved pressure residual;
- thermal residuals: heater transfer, cooler/HX removal, passive wall loss,
  bare-quartz test-section source/loss, junction/stub heat, external
  convection/radiation, optional storage/future term, internal-Nu diagnostic,
  and unresolved thermal residual.

The residual table contract is `residual_attribution_contract.csv`.

## Do-Not-Do Guardrails

- Do not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty,
  realized test-section heat, validation temperatures, holdout temperatures, or
  external-test temperatures as predictive runtime inputs.
- Do not re-open the broad heater/cooler/wall blocker; the active blocker is
  the narrower wall/test-section/passive-boundary thermal-shape blocker.
- Do not fit F6, ordinary upcomer `Nu`, ordinary upcomer `f_D`, or component K
  from recirculating rows.
- Do not clip negative K or hide pressure mismatch in a global friction
  multiplier.
- Do not hide external heat loss, cooler error, heater efficiency, or
  junction/stub loss in internal Nu.
- Do not release Salt2 +/-5Q, `val_salt2`, PM10, future +/-10Q, or new CFD into
  fitting or model selection.

## Next Agent Sequence

1. Implement the baseline scorecard runner from the shell without changing
   model physics.
2. Build or refresh the external boundary dictionary contract against current
   `fluid+walls` segment roles.
3. Run the pressure source-envelope/basis audit before any hydraulic fitting.
4. Align the heat-loss network and wall/test-section candidate contracts before
   any coupled grid.
5. Add recirculation guards and hybrid exchange-cell residual columns before
   interpreting upcomer/corner rows.
6. Freeze a candidate only after source/property labels, runtime audit,
   hydraulic gates, thermal gates, sensor-map policy, and recirculation guards
   pass.

