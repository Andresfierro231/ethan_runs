---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/summary.json
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/summary.json
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/summary.json
  - work_products/2026-07/2026-07-17/2026-07-17_wall_passive_test_section_admission_closeout/summary.json
tags: [thesis, model-form-bakeoff, final-split, endpoint-strategy]
related:
  - TODO-THESIS-ENDPOINT-MODEL-FORM-BAKEOFF
  - final-predictive-split-policy
  - predictive-wall-test-section-submodels
task: TODO-THESIS-ENDPOINT-MODEL-FORM-BAKEOFF
date: 2026-07-17
role: Writer/Reviewer/Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester
type: work_product
status: complete
---
# Thesis Endpoint Model-Form Bakeoff

## Result

This package scores and documents thesis-ready intermediate model forms M0-M4
under the locked final predictive split. It does not run solvers, fit models, or
change admission state.

## Predictive vs Diagnostic

- `M0` is a predictive setup-only baseline shell, but its numeric predictions
  are missing.
- `M1` is diagnostic replay. It can explain heat placement but cannot be a
  predictive claim.
- `M2` has admitted heater and cooler/HX boundary terms, but the full
  wall/test-section predictive model remains blocked.
- `M3` is the main segment-only `fluid+walls` network comparison, currently
  blocked for final scoring by the missing Salt1-4 nominal freeze and physics
  blockers.
- `M4` is the junction-aware `fluid+walls` extension. It supports attribution
  claims, but current pressure corner-K and junction coefficients remain
  diagnostic with zero fit-admitted rows.

## Thesis-Safe Claims

The thesis can claim that the endpoint ladder is defined, guarded by the locked
split, and partially scored where prior diagnostic or admitted submodel evidence
exists. It can claim M2 heater/cooler submodel admission and M4 junction-aware
attribution value. It cannot claim final frozen predictive performance, M1
predictivity, or admitted corner-K/junction coefficients.

## Outputs

- `model_form_contracts.csv`
- `model_form_scores.csv`
- `model_form_costs.csv`
- `model_form_failure_modes.csv`
- `thesis_claim_ledger.csv`
- `runtime_leakage_audit.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Model forms represented: `5`.
- Numeric legacy/partial score rows: `4`.
- Prediction-missing or blocked score rows: `4`.
- Runtime audit failures: `0`.
