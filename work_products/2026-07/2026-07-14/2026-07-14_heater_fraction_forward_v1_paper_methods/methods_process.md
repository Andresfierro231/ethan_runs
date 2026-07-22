---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_contract_interpretation.csv
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_heat_ledger.csv
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv
  - work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/summary.json
tags: [forward-model, boundary-modeling, heater-source, paper-methods]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: AGENT-390
date: 2026-07-14
role: BC-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Paper Methods Process

## Objective

This package documents the first executable source-contract slice of the
forward-v1 completion plan. It converts the heater/test-section source decision
into a split-aware screen that can be cited in a scientific paper without
claiming final predictive-HX admission.

## Governing Balance

The source contract is interpreted through the segment heat balance:

```text
mdot * cp * (T_out - T_in) =
    Q_heater - Q_cooler - Q_passive - Q_storage - Q_residual
```

For this slice, cooler/HX and passive external losses remain separate lanes.
The tested heater/source perturbation is:

```text
delta_Q = (eta_heater - 1) * P_heater_setup
          - test_section_external_loss_W
          + test_section_fluid_fraction * P_test_section_setup
```

The existing heater-contract package provides a local linear sensitivity:

```text
Tmean_error_model = Tmean_error_heater_only + S_case * delta_Q
```

where `S_case` is the case-specific `test_source_sensitivity_K_per_W`.

## Split And Fitting Policy

Salt2 is the only fitting row. Salt3 is validation. Salt4 is holdout. The
package fits at most one scalar at a time:

- `eta_heater` for `H1_eta_heater_fit_salt2`;
- `test_section_external_loss_W` for
  `H2_test_section_external_loss_fit_salt2`.

The 37 W test-section source form is retained only as a rejected comparison.
Validation and holdout temperatures are never used to set fitted values.

## Runtime Input Discipline

The package does not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD
cooler duty, or held-out temperatures as predictive runtime inputs. Realized
heater/test-section `wallHeatFlux` remains diagnostic evidence only. The source
scores are still blocked from final forward-v1 admission because the underlying
evidence is an imposed-cooler forward-v0 source screen, not a setup-only HX
model.

## Result

- Best current unfitted source contract: heater-only.
- Train-only scalar candidates scored: `2`.
- Final forward-v1 admitted here: `false`.
- Held-out mean absolute Tmean error for heater-only:
  `5.753 K`.
- Held-out mean absolute Tmean error for Salt2-fitted `eta_heater`:
  `3.199 K`.
- Held-out mean absolute Tmean error for Salt2-fitted test-section loss:
  `3.612 K`.

## Paper Use

This is suitable for a paper methods/results subsection on source-contract
screening and predictive-input discipline. It is not suitable as a final
forward-v1 scorecard or as proof that the cooler/HX boundary has been solved.
