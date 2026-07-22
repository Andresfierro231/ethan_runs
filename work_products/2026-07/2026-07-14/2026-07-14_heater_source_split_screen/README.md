---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_contract_interpretation.csv
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/candidate_parameters.csv
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/recommended_model.csv
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv
tags: [boundary-modeling, heater-source, forward-model, validation-split]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_heater_source_split_screen/heater_source_split_score_rows.csv
  - work_products/2026-07/2026-07-14/2026-07-14_heater_source_split_screen/heater_source_parameter_screen.csv
task: AGENT-332
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Source Split Screen

## Purpose

This package executes `BCM-HEATER-FRACTION-V1` using existing
heater/test-section contract evidence. It fits at most one scalar on Salt2 and
scores Salt3 validation plus Salt4 holdout. It does not rerun Fluid.

## Math

The source contract is:

```text
Q_to_fluid = eta_heater * P_heater_setup
           + f_test * P_test_section_setup
           - Q_test_section_external_loss
           - Q_cooler
           - Q_passive_external
```

For this screen, `Q_cooler` and passive external losses remain separate
boundary lanes. The linearized temperature score uses the existing
heater-contract sensitivity:

```text
T_pred = T_heater_only + S_test_source * DeltaQ
DeltaQ = (eta_heater - 1) * P_heater_setup
       + f_test * P_test_section_setup
       - Q_test_section_external_loss
```

## Results

- `C1_heater_only_unfitted` remains the recommended setup-only source contract.
- `C2_eta_heater_fit_salt2` reduces Salt3/Salt4 mean absolute Tmean proxy
  error by `2.553 K` versus C1.
- `C3_test_section_external_loss_fit_salt2` reduces Salt3/Salt4 mean absolute
  Tmean proxy error by `2.140 K` versus C1.
- Both fitted scalar forms remain proxy-screen candidates, not final
  forward-v1 admissions.

## Guardrails

Realized CFD wallHeatFlux, CFD cooler duty, CFD mdot, and validation/holdout
temperatures are not runtime inputs. CFD Tmean appears only as a Salt2 fitting
target or Salt3/Salt4 scoring target.

## Next Executable Task

Use `C1_heater_only_unfitted` as the default source contract in the next full
Fluid scorecard. If testing a calibrated source scalar, choose exactly one of
`C2_eta_heater_fit_salt2` or `C3_test_section_external_loss_fit_salt2`, fit it
on Salt2 only, and report Salt3/Salt4 branch and sensor errors without refit.
